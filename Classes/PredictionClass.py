import datetime
import math
import re
import queue
from time import perf_counter

from Classes.DynamicPredictorClass import DynamicPredictor
from Classes.soup_operations import cal_length, cal_depth, get_siblings_soup, remove_link_prefix, \
    position_in_level, link_tags, get_siblings_attr, ignored_list, find_soup_root


def element_stability_prediction_attribute(DP, element, distance_from_element, attributes=None):
    counter = 1
    if str(type(element)) == "<class 'NoneType'>":
        return None, 0
    length = cal_length(element, True)
    depth = cal_depth(element)
    highest_robustness = -1
    returned_attribute = None
    attributes = attributes if attributes else element.attrs
    for attribute in attributes:
        position = counter
        if attribute == "class":
            nr_children = len(element.attrs[attribute])
        else:
            nr_children = 1
        nr_siblings = len(element.attrs) - 1
        # lxpath = len(xpath_soup(element).split("/")) + 1
        X_test = [(position, length, depth, nr_siblings, nr_children, True)]
        prediction_1 = DP.model.predict(X_test)
        prediction = 1.0 - prediction_1
        if prediction * math.pow(dfactor, distance_from_element) > highest_robustness:
            highest_robustness = prediction * math.pow(dfactor, distance_from_element)
            returned_attribute = attribute
        counter += counter + 1
    assert returned_attribute is not None
    return returned_attribute, highest_robustness


def element_stability_prediction_soup(DP, element, distance_from_element=None):
    length = cal_length(element, True)
    depth = cal_depth(element)
    nr_children = len(element.contents) + len(element.attrs)
    position, siblings_vector, nr_siblings = get_siblings_soup(element)
    # lxpath = len(xpath_soup(element).split("/"))
    X_test = [(position, length, depth, nr_siblings, nr_children, False)]
    prediction = 1 - DP.model.predict(X_test)
    # prediction = prediction * math.pow(0.95, distance_from_element)
    return prediction


dfactor=0.95

timestamped_attributes = ["href", "data-analytics-view-custom-item-id", "data-h", "alt", "data-story-id",
                          "data-lazy-load-path", "data-url", "data-m","action",
                          "data-post-id", "data", "data-post-id", "src", "srcset", "aria-label", "data-id",
                          "data-video-id",
                          "data-sprite", "data-src-swiper", "style", "data-dsqu","url"]


def find_closest_unique_elements(DP, soup_element):
    child = soup_element
    sc = None
    for parent in child.parents:
        child = parent
    root = child
    distance = 0
    results = root.find_all(soup_element.name, limit=2)
    if len(results) == 1:
        return results, None, None
    else:
        unique_attributes = []
        for attribute in soup_element.attrs:
            if attribute in timestamped_attributes or attribute[:4] == "data":
                continue
            if attribute == "class":
                if len(soup_element.attrs[attribute]) == 0:
                    continue
                for c in range(0, len(soup_element.attrs[attribute])):
                    unique, lsc = root.find_all(attrs={attribute: soup_element.attrs[attribute][c]}, limit=2), c
                    if len(unique) == 1:
                        sc = lsc
            else:
                unique = root.find_all(attrs={attribute: soup_element.attrs[attribute]}, limit=2)
            if len(unique) == 1:
                unique_attributes.append(attribute)
        if len(unique_attributes) > 1:
            attribute, AttributeRobustness = element_stability_prediction_attribute(DP, soup_element, distance,
                                                                                    unique_attributes)
            if attribute == "class":
                unique = root.find_all(attrs={attribute: soup_element.attrs[attribute][sc]}, limit=2)
            else:
                unique = root.find_all(attrs={attribute: soup_element.attrs[attribute]}, limit=2)
            return unique, attribute, sc
        elif len(unique_attributes) == 1:
            if unique_attributes[0] == "class":
                unique = root.find_all(attrs={unique_attributes[0]: soup_element.attrs[unique_attributes[0]][sc]},
                                       limit=2)
            else:
                unique = root.find_all(attrs={unique_attributes[0]: soup_element.attrs[unique_attributes[0]]}, limit=2)
            return unique, unique_attributes[0], sc
    for parent in soup_element.parents:
        distance += 1
        results = root.find_all(parent.name, limit=2)
        if len(results) == 1:
            return results, None, sc
        else:
            unique_attributes = []
            for attribute in parent.attrs:
                if attribute in timestamped_attributes:
                    continue
                if attribute == "class":
                    for c in range(0, len(parent.attrs[attribute])):
                        unique, lsc = root.find_all(attrs={attribute: parent.attrs[attribute][c]}, limit=2), c
                        if len(unique) == 1:
                            unique_attributes.append(attribute)
                            sc = lsc
                            continue
                else:
                    unique = root.find_all(attrs={attribute: parent.attrs[attribute]}, limit=2)
                if len(unique) == 1:
                    unique_attributes.append(attribute)
            if len(unique_attributes) > 1:
                attribute, AttributeRobustness = element_stability_prediction_attribute(DP, parent, distance,
                                                                                        unique_attributes)
                if attribute == "class":
                    unique = root.find_all(attrs={attribute: parent.attrs[attribute][sc]}, limit=2)
                else:
                    unique = root.find_all(attrs={attribute: parent.attrs[attribute]}, limit=2)
                return unique, attribute, sc
            elif len(unique_attributes) == 1:
                if unique_attributes[0] == "class":
                    unique = root.find_all(attrs={unique_attributes[0]: parent.attrs[unique_attributes[0]][sc]},
                                           limit=2)
                else:
                    unique = root.find_all(attrs={unique_attributes[0]: parent.attrs[unique_attributes[0]]}, limit=2)
                return unique, unique_attributes[0], sc
    return root, None, sc




# We first calculate the robustness of all the attributes of an element,
# as we go through the attributes we calculate their robustness and save the highest one of them all.
# We keep the highest robustness saved all the time as we search for a more robust locator
def generate_locating_strategy(DP, soup_element, max_depth):
    robustness = 1
    highest_robustness = 0
    current_element = soup_element
    xpath_list = []
    saved_attribute = None
    distance = 0
    Flag = True
    popcount = 0
    while True:
        robustness = highest_robustness
        attribute, AttributeRobustness = element_stability_prediction_attribute(DP, current_element,
                                                                                distance)
        soupElementRobustness = element_stability_prediction_soup(DP, current_element, distance)
        position = get_siblings_soup(current_element, True)
        if soupElementRobustness > highest_robustness and soupElementRobustness > AttributeRobustness:
            highest_robustness = soupElementRobustness
            xpath_list.append((current_element, position, highest_robustness))
            if attribute is not None:
                saved_attribute = attribute
                Flag = True
                popcount = 0
            else:
                Flag = False
                popcount += 1
        elif AttributeRobustness > highest_robustness:
            highest_robustness = AttributeRobustness
            xpath_list.append((current_element, attribute, highest_robustness))
            saved_attribute = attribute
            Flag = True
            popcount = 0

        # str(type(current_element.parent)) == "<class 'NoneType'>"
        if robustness == highest_robustness and Flag or current_element.name == "html":
            if current_element.name == "html":
                xpath_list.append((current_element, position, highest_robustness))
                break
            for i in range(0, popcount):
                xpath_list.pop()
            last_element = xpath_list[len(xpath_list) - 1][0]
            xpath_list.pop()
            if saved_attribute not in last_element.attrs:
                print()
            xpath_list.append((last_element, saved_attribute, highest_robustness))
            break
        elif attribute is not None and not Flag:
            highest_robustness = AttributeRobustness
            xpath_list.append((current_element, attribute, highest_robustness))
            saved_attribute = attribute
            Flag = True
            popcount = 0
        current_element = current_element.parent
        distance += 1

    if len(xpath_list) == 1:
        if xpath_list[0][1] is not None:
            if saved_attribute == "class":
                class_value = soup_element.attrs[saved_attribute][0]
                xpath_string = "//*" + '[contains(@class ,"' + class_value + '")]'
            elif saved_attribute in link_tags:
                xpath_string = "//*" + "[@" + saved_attribute + '="' + \
                               remove_link_prefix(soup_element.attrs[saved_attribute]) + '"]'
            else:
                xpath_string = "//*[@" + saved_attribute + '="' + soup_element.attrs[
                    saved_attribute] + '"]'
            return xpath_string
    else:
        xpath_string = "/"
        for path_element in reversed(xpath_list):
            if type(path_element[1]) != int:
                if path_element[1] == "class":
                    xpath_string += '/*[contains(@class ,"' + path_element[0].attrs[path_element[1]][0] \
                                    + '")]' + position_in_level(path_element)
                elif type(path_element[0].attrs[path_element[1]]) == list:
                    xpath_string += '/*[@' + path_element[1] + '="' + path_element[0].attrs[path_element[1]][0] \
                                    + '"]' + position_in_level(path_element)
                else:
                    xpath_string += '/*[@' + path_element[1] + '="' + path_element[0][
                        path_element[1]] + '"]' + position_in_level(path_element)
            else:
                if path_element[1] > 1:
                    xpath_string += "/" + path_element[0].name + '[' + str(path_element[1]) + ']'
                else:
                    xpath_string += "/" + path_element[0].name

        return xpath_string


def generate_locators_prediction_model(bf_elements, model_name, scaled=False):
    dom = find_soup_root(bf_elements[0])
    XC = XpathClass(model_name, dom, scaled)
    locators_list = []
    time_RELOC = []

    if len(bf_elements) > 1:
        for element in bf_elements:
            XC.reset_class()
            start_time = perf_counter() # Start timing for this element
            try:
                locators_list.append(XC.generate_locating_strategy_Xpath(element))
            except Exception as e:
                print(e)
            end_time = perf_counter() # End timing for this element
            elapsed_time = end_time - start_time
            time_RELOC.append(elapsed_time)

    else:

        start_time = perf_counter()  # Start timing for this element
        try:
            locators_list.append(XC.generate_locating_strategy_Xpath(bf_elements[0]))
        except Exception as e:
            print(e)
        end_time = perf_counter() # End timing for this element
        elapsed_time = end_time - start_time
        time_RELOC.append(elapsed_time)

    return locators_list, time_RELOC

def match_path_element(current_element, path_element):
    match_class = re.search(r'\[contains\(concat\(" ", normalize-space\(@class\), " "\), " (.*?) "\)\](\[(\d+)\])?',
                            path_element)
    if match_class:
        class_value = match_class.group(1)
        position = match_class.group(3)
        if position and position != "1":
            elements = current_element.find_all(attrs={"class": class_value}, recursive=False)[int(position) - 1]
        else:
            elements = current_element.find_all(attrs={"class": class_value})
        return elements

    # Check if this part specifies an element by tag name
    match_attribute = re.search(r'\*?\[@(.*?)="(.*?)"](\[(\d+?)\])?', path_element)

    if match_attribute:
        attribute_name = match_attribute.group(1)
        value = match_attribute.group(2)
        position = match_attribute.group(4)
        if position and position != "1":
            elements = current_element.find_all(attrs={attribute_name: value}, recursive=False)[int(position) - 1]
        else:
            elements = current_element.find_all(attrs={attribute_name: value})
        return elements

    match_tag = re.search(r'\*?([a-zA-Z]*)(\[(\d+?)\])?', path_element)
    if match_tag:
        tag_name = match_tag.group(1)
        position = match_tag.group(3)
        if position and position != "1":
            elements = current_element.find_all(tag_name, recursive=False)[int(position) - 1]
        else:
            elements = current_element.find_all(tag_name)
        return elements


def find_element_by_xpath(xpath, soup):
    parts = re.split(r'//\*|/\*', xpath)

    current_element = soup
    my_queue = queue.Queue()
    my_queue2 = queue.Queue()
    # Iterate through the XPath parts
    for part in parts:

        # Skip empty parts (e.g., leading slashes)
        if not part:
            continue
        if not my_queue.empty():
            while not my_queue.empty():
                current_element = my_queue.get()
                try:
                    elements = match_path_element(current_element, part)
                except IndexError:
                    print("error")
                if str(type(elements)) != "<class 'bs4.element.Tag'>":
                    for element in elements:
                        my_queue2.put(element)
                else:
                    my_queue2.put(elements)
        else:
            # Use regular expressions to extract class and position
            try:
                elements = match_path_element(current_element, part)
            except IndexError:
                print("error")
            for element in elements:
                my_queue2.put(element)

        my_queue = my_queue2
        my_queue2 = queue.Queue()
    if my_queue.empty():
        return False
    # Return the first matching element found
    else:
        current_element = my_queue.get()
        return current_element


class XpathClass:
    xpath_list = []
    dict_list = []
    DP = DynamicPredictor()
    max_position = 0
    max_children = 0
    max_siblings = 0
    maximum_length = 0
    dom = None
    scaled = False

    def __init__(self, model, dom, scaled=False):
        self.xpath_list = []
        self.scaled = scaled
        self.dom = dom
        path=model
        self.DP.load_model(path)

    def cal_maximums(self):
        root = self.dom.find("body")
        max_children = 0
        max_siblings = 0
        maximum_length = cal_length(root)
        for child in root.descendants:
            if (str(type(child))) in ignored_list:
                continue
            if child == '\n':
                continue
            if len(child.contents) > max_children:
                max_children = len(child.contents)
            if len(child.contents) > max_siblings:
                max_siblings = len(get_siblings_soup(child))
        self.max_children = max_children
        self.maximum_length = maximum_length + 1
        self.max_siblings = max_siblings
        self.max_position = max_siblings + 1
        return

    def reset_class(self):
        self.xpath_list = []
        self.dict_list = []

    def element_stability_prediction(self, element, distance):
        length = cal_length(element, True)
        depth = cal_depth(element)
        nr_children = len(element.contents) + len(element.attrs)
        position, siblings_vector, nr_siblings = get_siblings_soup(element)
        # lxpath = len(xpath_soup(element).split("/"))
        if not self.scaled:
            X_test = [(position, length, depth, nr_siblings, nr_children, False)]
        else:
            X_test = [(position / self.max_position, length / self.maximum_length, depth / self.maximum_length,
                       nr_siblings / self.max_siblings, nr_children / self.max_children, False)]
        prediction = self.DP.model.predict(X_test)
        prediction = prediction * math.pow(dfactor, distance)
        element_dict = {"soup": element, element.name: prediction}
        for attr in element.attrs:
            if attr in timestamped_attributes:
                continue
            length = cal_length(element, True) + 1
            depth = 0
            nr_children = 1
            position = get_siblings_attr(element, attr)
            # lxpath = len(xpath_soup(element).split("/"))
            if not self.scaled:
                X_test = [(position, length, depth, len(element.attrs) - 1, nr_children, True)]
            else:
                X_test = [(position / self.max_position, length / self.maximum_length, depth / self.maximum_length,
                           nr_siblings / self.max_siblings, nr_children / self.max_children, True)]
            prediction = 1 - self.DP.model.predict(X_test)
            prediction = prediction * math.pow(dfactor, distance)
            element_dict[attr] = prediction
        return element_dict

    def generate_locating_strategy_Xpath(self, soup_element):
        first_unique_element, saved_attribute, sc = find_closest_unique_elements(self.DP, soup_element)
        assert len(first_unique_element) == 1
        current_element = soup_element
        distance = 0
        if first_unique_element[0] != soup_element:
            while True:
                prediction = self.element_stability_prediction(current_element, distance)
                self.xpath_list.append(prediction)
                if first_unique_element[0] == current_element:
                    break
                current_element = current_element.parent
                distance += 1
        if saved_attribute is None:
            xpath = [(len(self.xpath_list) - 1, first_unique_element[0].name, saved_attribute, 1)]
        else:
            if saved_attribute == "class":
                xpath = [
                    (len(self.xpath_list) - 1, saved_attribute, first_unique_element[0].attrs[saved_attribute][sc],
                     None)]
            else:
                xpath = [
                    (len(self.xpath_list) - 1, saved_attribute, first_unique_element[0].attrs[saved_attribute], None)]
        if first_unique_element[0] != soup_element:
            xpath = xpath + self.generate_reloc_xpath()
        assert (len(xpath) != 0)
        xpath_string = "/"
        if len(xpath) == 1:
            if saved_attribute == "class":
                xpath_string += '/*[contains(concat(" ", normalize-space(@class), " "), " ' + \
                                first_unique_element[0].attrs[saved_attribute][sc] + ' ")]'
            else:
                if first_unique_element[0].has_attr(saved_attribute):
                    xpath_string += '/*[@' + saved_attribute + '="' + first_unique_element[0].attrs[
                        saved_attribute] + '"]'
                else:
                    xpath_string += '/' + first_unique_element[0].name
        else:
            assert (self.xpath_list[xpath[len(xpath) - 1][0]]["soup"] == soup_element)
            for level in xpath:
                if level[3] == -1:
                    xpath_string += '/'
                if level[2] is not None:
                    if level[1] == "class":
                        xpath_string += '/*[contains(concat(" ", normalize-space(@class), " "), " ' + \
                                        level[2] + ' ")]'
                    else:
                        xpath_string += '/*[@' + level[1] + '="' + self.xpath_list[level[0]]["soup"].attrs[
                            level[1]] + '"]'
                    if level[3] and level[3] != -1:
                        xpath_string += '[' + str(level[3]) + ']'
                else:
                    pos, flag = get_siblings_soup(self.xpath_list[level[0]]["soup"], True)
                    if flag:
                        xpath_string += '/' + level[1] + "[" + str(pos) + "]"
                    else:
                        xpath_string += '/' + level[1]
        # assert find_element_by_xpath(xpath_string, self.dom) == soup_element
        return xpath_string

    def find_element_by_xpath(xpath, soup):
        """
        Find an element in a BeautifulSoup-parsed DOM using an XPath-like expression.

        :param xpath: XPath-like expression to locate the element.
        :param soup: BeautifulSoup-parsed DOM.
        :return: The first matching element or None if not found.
        """
        # Split the XPath into individual parts
        parts = xpath.split('//')

        # Start from the root of the DOM
        current_element = soup

        # Iterate through the XPath parts
        for part in parts:
            # Skip empty parts (e.g., leading slashes)
            if not part:
                continue

            # Check if this part specifies an element by tag name
            tag_name, _, attributes = part.partition('/')

            # Find all elements with the given tag name
            elements = current_element.find_all(tag_name)

            if attributes:
                # Filter elements based on attributes (if any)
                attribute_filter = attributes.strip('/')
                elements = [element for element in elements if attribute_filter in str(element)]

            # If we couldn't find any matching elements, return None
            if not elements:
                return None

            # Update the current element for the next iteration
            current_element = elements[0]

        # Return the first matching element found
        return current_element

    def element_position(self, element):
        count = 0
        for index, sibling in enumerate(element.previous_siblings):
            count += 1
        return count

    def generate_xpath(self, soup_element):
        element_list = []
        child = soup_element if soup_element.name else soup_element.parent
        for parent in soup_element.parents:
            element_list.append(child)
        return element_list.reverse()

    def generate_reloc_xpath(self):
        last_xpath_element = self.xpath_list[len(self.xpath_list) - 1]["soup"]
        index, last_index, attribute, index_value, unique = len(self.xpath_list) - 2, len(
            self.xpath_list) - 1, None, None, 0
        greedy_xpath = []
        selected_class = None
        while index != -1:
            highest_prediction = -1
            div_list = []
            for i in range(index, -1, -1):
                for key, value in self.xpath_list[i].items():
                    if key == "href" or key == "soup" or key in timestamped_attributes:
                        continue
                    if self.xpath_list[i]["soup"].has_attr(key):
                        if not self.xpath_list[i]["soup"].attrs[key]:
                            continue
                        if i == last_index - 1:
                            if key == "class":
                                local_uniqueness = 10000000
                                for one_class in self.xpath_list[i]["soup"].attrs[key]:
                                    uniqueness, position = cal_position(last_xpath_element, self.xpath_list[i]["soup"],
                                                                        key,
                                                                        one_class, multilevel=False)
                                    if uniqueness < local_uniqueness:
                                        selected_class = one_class
                                        local_uniqueness = uniqueness
                                        class_index = i
                                uniqueness = local_uniqueness

                            else:
                                uniqueness, position = cal_position(last_xpath_element, self.xpath_list[i]["soup"], key,
                                                                    self.xpath_list[i]["soup"].attrs[key],
                                                                    multilevel=False)
                        else:
                            if key == "class":
                                local_uniqueness = 10000000
                                for one_class in self.xpath_list[i]["soup"].attrs[key]:
                                    uniqueness, position = cal_position(last_xpath_element, self.xpath_list[i]["soup"],
                                                                        key,
                                                                        one_class, multilevel=False)
                                    if uniqueness < local_uniqueness:
                                        selected_class = one_class
                                        local_uniqueness = uniqueness
                                        class_index = i
                                uniqueness = local_uniqueness
                            else:
                                uniqueness, position = cal_position(last_xpath_element, self.xpath_list[i]["soup"], key,
                                                                    self.xpath_list[i]["soup"].attrs[key],
                                                                    multilevel=True)
                        robustness = math.pow(value, uniqueness)
                    else:
                        if i == last_index - 1:
                            uniqueness, position = cal_position(last_xpath_element, self.xpath_list[i]["soup"],
                                                                multilevel=False)
                            robustness = math.pow(value, uniqueness)
                        else:
                            robustness = 1
                            uniqueness = 1
                            pos_list = {}
                            for j in range(i, last_index):
                                uniqueness_factor, position = cal_position(self.xpath_list[j + 1]["soup"],
                                                                           self.xpath_list[j]["soup"],
                                                                           multilevel=False)
                                uniqueness = uniqueness_factor * uniqueness
                                robustness_factor = math.pow(value, uniqueness)
                                robustness = robustness_factor * robustness
                                pos_list[j] = position
                    if robustness > highest_prediction and position is not None:
                        if self.xpath_list[i]["soup"].has_attr(key):
                            if key == "class":
                                # index, attribute, index_value, unique = i, key, self.xpath_list[i]["soup"].get('class') \
                                #     , position
                                index, attribute, index_value, unique = class_index, key, selected_class, position
                            else:
                                index, attribute, index_value, unique = i, key, self.xpath_list[i]["soup"].attrs[
                                    key], position
                            div_list = []
                            highest_prediction = robustness
                        else:
                            if i == last_index - 1:
                                index, attribute, index_value, unique = i, key, None, position
                                highest_prediction = robustness
                                div_list = []
                            else:
                                div_list = []
                                for j in range(last_index - 1, i - 1, -1):
                                    index, attribute, index_value, unique = j, self.xpath_list[j]["soup"].name, None, \
                                        pos_list[j]
                                    div_list.append((index, attribute, index_value, unique))
                                highest_prediction = robustness
            if div_list:
                greedy_xpath = greedy_xpath + div_list
            else:
                greedy_xpath.append((index, attribute, index_value, unique))
            last_xpath_element = self.xpath_list[index]['soup']
            last_index = index
            index = index - 1
        assert (greedy_xpath[len(greedy_xpath) - 1][0] == 0)
        return greedy_xpath


# def cal_uniqnuess(root, element, attribute=None, text_content=None, multilevel=False):


def cal_position(root, element, attribute=None, text_content=None, multilevel=False):
    position = 0
    if multilevel:
        if attribute:
            if attribute == "class":
                uniqueness = len(root.select('.' + text_content[0]))
            else:
                uniqueness = len(root.find_all(attrs={attribute: text_content}))
        else:
            uniqueness = len(root.find_all(element.name))
    else:
        if attribute:
            uniqueness = len(root.find_all(attrs={attribute: text_content}, recursive=False))
        else:
            uniqueness = len(root.find_all(element.name, recursive=False))
    count = 1
    if attribute:
        elements = root.find_all(attrs={attribute: text_content}, recursive=False)
    else:
        elements = root.find_all(element.name, recursive=False)
    for i, e in enumerate(elements):
        if e is element:
            position = i + 1
            break
    if multilevel and uniqueness == 1:
        return uniqueness, -1
    elif position < 1:
        return uniqueness, None
    return uniqueness, position


def remove_special_characters(character):
    if character.isascii() or character == ' ':
        return True
    else:
        return False
