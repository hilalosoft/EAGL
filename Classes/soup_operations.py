import itertools
import re

from sklearn.preprocessing import MinMaxScaler
from selenium.webdriver.common.by import By
from time import perf_counter
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import datetime
from timeout_decorator import timeout, TimeoutError



link_tags = ["src", "a", "action", "href"]

ignored_list = ["<class 'bs4.element.Script'>",
                "<class 'bs4.element.Stylesheet'>",
                "<class 'bs4.element.Comment'>",
                "<class 'bs4.element.Declaration'>",
                "<class 'bs4.element.TemplateString'>",
                "<class 'bs4.element.NavigableString'>",
                "<class 'bs4.element.Doctype'>",
                "<class 'bs4.element.ProcessingInstruction'>",
                "<class 'bs4.element.CData'>"]

considered_tag_dictionary = {"id": 0, "string": 0, "ul": 0, "li": 0, "h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0,
                             "div": 0, "span": 0, "form": 0, "input": 0, "p": 0, "img": 0, 'a': 0, "dl": 0, "dt": 0, "dd": 0, "svg": 0, "path": 0, "g": 0
    , "option": 0, "i": 0, "attribute": 0, "button": 0, "class": 0, "href": 0, "other": 0}


# we copy the dictionary containing considered tags iterate over all the siblings,
# determine the element position within its peers and divide in the end on the number of siblings to normalize.
# normalize the position in the end
def get_siblings_soup(soup, cal_pos=False):
    siblings_dict = considered_tag_dictionary.copy()
    count = 1
    if cal_pos:
        flag = False
        for index, sibling in enumerate(soup.previous_siblings):
            if sibling.name == soup.name:
                count += 1
                flag = True
        for index, sibling in enumerate(soup.next_siblings):
            if sibling.name == soup.name:
                flag = True
                break
        return count, flag
    for index, sibling in enumerate(itertools.chain(soup.previous_siblings, soup.next_siblings)):
        if sibling.name in siblings_dict:
            siblings_dict[sibling.name] += 1
        else:
            siblings_dict["other"] += 1
        count += 1

    for key in siblings_dict:
        siblings_dict[key] = siblings_dict[key] / count
    position = (sum(1 for _ in soup.previous_siblings) + 1) / count
    return position, siblings_dict, count


def get_siblings_attr(soup, attr):
    count = 0
    for attribute in soup.attrs:
        count += 1
        if attribute == attr:
            return count / len(soup.attrs)


# The function takes an element as input and returns an xpath string representation of the element, which can be used
# to locate the element in an XML or HTML document. The xpath is constructed by iterating over all the parents of the
# element, adding the element name to the path, and if there are multiple elements with the same name, adding the
# index of the element to the path.
def xpath_soup(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


# the function takes a dom object as input
# returns the maximum depth of the dom object by iterating through all the descendants of the dom
# ignoring certain tags and adding 1 to the maximum depth if the child has any attributes.
# This helps to find the depth of the HTML tree structure.
def cal_depth(dom):
    maximum_length = 0
    for child in dom.children:
        if child == '\n':
            continue
        child_depth = cal_length(child)
        if child_depth > maximum_length:
            maximum_length = child_depth
            if (str(type(child)) not in ignored_list and
                    len(child.attrs) > 0):
                maximum_length += maximum_length + 1
    return maximum_length


# in case max depth is not given then the calculation is not for the feature vector
# flag is to check if the element is attribute or not
def cal_length(soup, flag=False):
    count = 0
    if soup.name == "html":
        return count
    for parent in soup.parents:
        count += 1
    if flag:
        count += 1
    return count


def generate_vector(node, node_value, timestamp, position, length, depth, nr_siblings, nr_children, xpath, isattribute,
                    changed):
    vector = [node, node_value, timestamp, position, length, depth, nr_siblings, nr_children, xpath, isattribute,
              changed]
    return vector


def generate_vectors_from_navigable_string(next_dom, timestamp, soup, index):
    xpath = xpath_soup(soup)
    changed = element_changed(next_dom, xpath, soup, text_content=soup.string)
    length = cal_length(soup)
    depth = cal_depth(soup)
    vector = generate_vector("string", "", timestamp, index, length, depth, 0, 0, xpath, True, changed)
    return vector


def generate_vectors_from_soup(next_dom, timestamp, soup):
    nr_of_children = len(soup.contents) + len(soup.attrs)
    position, siblings_vector, nr_siblings = get_siblings_soup(soup)
    xpath = xpath_soup(soup)
    length = cal_length(soup)
    vector_list = []
    soup_id = generate_vectors_for_attr(next_dom, timestamp, soup, xpath)
    if soup_id:
        vector_list.append(soup_id)
    changed = element_changed(next_dom, xpath, soup)
    depth = cal_depth(soup)
    vector_list.append(generate_vector(soup.name, "", timestamp, position,
                                       length, depth, nr_siblings, nr_of_children, xpath, False, changed))
    return vector_list


def generate_vectors_for_attr(next_dom, timestamp, soup, xpath):
    if "id" in soup.attrs:
        value = soup.attrs.get("id")
        length = cal_length(soup, True)
        changed = element_changed(next_dom, xpath, soup, attribute="id", text_content=value)
        depth = cal_depth(soup)
        return (generate_vector("id", str(value),
                                timestamp, 0, length, depth, len(soup.attrs) - 1, 0, xpath, True, changed))
    else:
        return False


def remove_link_prefix(link):
    if link:
        links = re.split('http://|https://', link)
        return links[len(links) - 1]
    else:
        return ""

def element_changed(next_dom, xpath, soup, attribute=None, text_content=None):
    if attribute:
        element_to_compare = next_dom.find_all(id=text_content)
    else:
        element_to_compare = find_element_by_xpath_soup(xpath, next_dom)
    if not element_to_compare:
        return True
    else:
        return False


def find_element_by_xpath_soup(xpath, next_dom):
    dom_element = next_dom
    xpath_list = xpath.split('/')[1:]
    flag = True
    for tag in xpath_list:
        if tag.find('[') != -1:
            try:
                position = int(tag[tag.find('[') + 1:tag.find(']')])
            except ValueError:
                continue
            tag = tag[:tag.find('[')]
        else:
            position = None
        count_position = 1
        for element in dom_element.contents:
            if position is None:
                if element.name == tag:
                    dom_element = element
                    flag = True
                    break
                else:
                    flag = False
            else:
                if element.name == tag:
                    if position == count_position:
                        dom_element = element
                        flag = True
                        break
                    else:
                        count_position += 1
                else:
                    flag = False
    if flag:
        return dom_element
    else:
        return False


class featureClass:
    feature_vectors = []
    feature_vectors_scaled = []
    feature_vectors_timestamp = []
    feature_vectors_timestamp_scaled = []
    none_tag = "textual_content"
    next_dom = None
    current_timestamp = None
    nr_elements = 0
    nr_changed_elements = 0

    def __init__(self):
        self.feature_vectors = []
        self.feature_vectors_timestamp = []
        self.feature_vectors_timestamp_scaled = []
        self.feature_vectors_scaled = []

    def reset_feature_vectors(self):
        self.feature_vectors = []
        self.feature_vectors_scaled = []

    def generate_feature_vector_dom(self, dom_list, timestamp_list, project_name):
        skipcounter = 1
        i = 0
        while i < len(dom_list) - 1:
            if i + skipcounter >= len(dom_list):
                break
            self.nr_elements = 0
            self.nr_changed_elements = 0
            self.current_timestamp = timestamp_list[i]
            try:
                parsed_dom = BeautifulSoup(dom_list[i], 'html.parser')
                body_soup = parsed_dom.find(["body"])
                extract_elements = body_soup.find_all()
                if len(extract_elements) <= 20:
                    i += 1
                    continue
            except (TypeError, AttributeError) as e:
                i += 1
                continue
            try:
                parsed_dom2 = BeautifulSoup(dom_list[i + skipcounter], 'html.parser')
                body_soup = parsed_dom2.find(["body"])
                extract_elements = body_soup.find_all()
                if len(extract_elements) <= 20:
                    skipcounter += 1
                    continue
            except (TypeError, AttributeError):
                skipcounter += 1
                continue
            self.next_dom = parsed_dom2
            self.compare_dom_recursive(parsed_dom.find(["body"]))
            # if self.nr_elements != 0 and self.nr_changed_elements / self.nr_elements > 0.7:
            #     skipcounter += 1
            # else:
            scaler = MinMaxScaler()
            self.feature_vectors_timestamp_scaled = np.array(self.feature_vectors_timestamp)
            for vector in self.feature_vectors_timestamp:
                self.feature_vectors.append(vector)

            # create scaled version of the data
            scaled_columns = self.feature_vectors_timestamp_scaled[:, [3, 4, 5, 6, 7]]
            scaled_columns = scaler.fit_transform(scaled_columns)
            self.feature_vectors_timestamp_scaled = np.concatenate(
                (self.feature_vectors_timestamp_scaled[:, [0, 1, 2]], scaled_columns[:, [0, 1, 2, 3, 4]],
                 self.feature_vectors_timestamp_scaled[:, [8, 9, 10]]), axis=1)
            self.feature_vectors_timestamp_scaled = self.feature_vectors_timestamp_scaled.tolist()
            for vector in self.feature_vectors_timestamp_scaled:
                self.feature_vectors_scaled.append(vector)

            i += skipcounter
            skipcounter = 1
            self.feature_vectors_timestamp = []
            self.feature_vectors_timestamp_scaled = []

        self.create_feature_csv(project_name)

    def create_feature_csv(self, project_name):
        header = ["node", "value", "timestamp", "position", "length", "depth", "nr_siblings", "nr_children", "xpath",
                  "isattribute", "changed"]
        full_list = []
        for feature_vector in self.feature_vectors:
            full_list.append(feature_vector)
        if full_list:
            df_tags = pd.DataFrame(full_list)
            df_tags.to_csv('data/feature_list_' + str(project_name) + '.csv', header=header, index=False)
        full_list = []
        for feature_vector in self.feature_vectors_scaled:
            full_list.append(feature_vector)
        if full_list:
            df_tags = pd.DataFrame(full_list)
            df_tags.to_csv('data/feature_list_' + str(project_name) + '_scaled.csv', header=header, index=False)
        return

    def set_comparing_dom(self, dom):
        self.next_dom = BeautifulSoup(dom, 'html.parser')

    def compare_dom_recursive(self, element):
        if str(type(element)) != "<class 'bs4.element.Tag'>":
            return
        if element.name in ["head", "script", "style"]:
            return
        for child_index, child in enumerate(element.contents, start=1):
            self.compare_dom_recursive(child)

        for feature_vector in generate_vectors_from_soup(self.next_dom, self.current_timestamp, element):
            self.nr_elements += 1
            if feature_vector[10]:
                self.nr_changed_elements += 1
            self.feature_vectors_timestamp.append(feature_vector)


def position_in_level(path_element):
    count = 1
    if type(path_element[1]) != int:
        if path_element[1] == "class":
            for index, sibling in enumerate(path_element[0].previous_siblings):
                try:
                    if sibling.name == path_element[0].name and path_element[0].attrs[path_element[1][0]] == \
                            sibling.attrs[
                                path_element[1][0]]:
                        count += 1
                except:
                    continue
        else:
            for index, sibling in enumerate(path_element[0].previous_siblings):
                try:
                    if sibling.name == path_element[0].name and path_element[0].attrs[path_element[1]] == sibling.attrs[
                        path_element[1]]:
                        count += 1
                except:
                    continue
    if count == 1:
        return ''
    else:
        return '[' + str(count) + ']'


def generate_locators_xpath(bf_elements):
    locators_list = []
    print(datetime.datetime.now())
    for element in bf_elements:
        if (str(type(element)) not in ignored_list and
                len(element.attrs) > 0):
            locators_list.append(xpath_soup(element))
    print(datetime.datetime.now())
    return locators_list



def find_soup_root(element):
    current_element = element
    while current_element.name != "html":
        current_element = current_element.parent
    return current_element
