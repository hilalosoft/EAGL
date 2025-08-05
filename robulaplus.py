import random
from bs4 import BeautifulSoup, Tag
from itertools import chain, combinations
from lxml import etree
from lxml.etree import XPathSyntaxError, XPathEvalError

import re
import threading


class TimeoutException(Exception):
    """Custom exception for handling timeouts."""
    pass


def timeout_decorator(timeout_duration):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Function to execute the target function
            def target_func(result, *args, **kwargs):
                result.append(func(*args, **kwargs))

            # Store the result of the function in a list to access it from the thread
            result = []
            thread = threading.Thread(target=target_func, args=(result, *args, *kwargs))
            thread.start()
            thread.join(timeout_duration)

            if thread.is_alive():
                # If the thread is still running after the timeout, raise an exception
                raise TimeoutException(f"Function execution exceeded {timeout_duration} seconds.")
            return result[0] if result else None

        return wrapper

    return decorator


class RobulaPlusOptions:
    def __init__(self, attribute_priorization_list=None, attribute_black_list=None):
        self.attribute_priorization_list = attribute_priorization_list or ['name', 'class', 'title', 'alt', 'value']
        self.attribute_black_list = attribute_black_list or [
            'href',
            'src',
            'onclick',
            'onload',
            'tabindex',
            'width',
            'height',
            'style',
            'size',
            'maxlength',
        ]


class XPath:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def starts_with(self, value):
        return self.value.startswith(value)

    def substring(self, value):
        return self.value[value:]

    def head_has_any_predicates(self):
        return '[' in self.value.split('/')[2]

    def head_has_position_predicate(self):
        split_xpath = self.value.split('/')
        return any(sub in split_xpath[2] for sub in ['position()', 'last()']) or any(
            char.isdigit() for char in split_xpath[2])

    def head_has_text_predicate(self):
        return 'text()' in self.value.split('/')[2]

    def add_predicate_to_head(self, predicate):
        split_xpath = self.value.split('/')
        split_xpath[2] += predicate
        self.value = '/'.join(split_xpath)

    def get_length(self):
        # Remove text inside predicates (between square brackets)

        cleaned_xpath = re.sub(r'\[.*?\]', '', self.value)

        # Split the remaining XPath by '/' and filter out empty strings
        segments = [piece for piece in cleaned_xpath.split('/') if piece]

        return len(segments)
    # def get_length(self):
    #     return len([piece for piece in self.value.split('/') if piece])


class ElementComparer:
    @staticmethod
    def normalize_attributes(attrs):
        normalized_attrs = {}
        for key, value in attrs.items():
            if key == 'class':
                if isinstance(value, str):
                    normalized_attrs[key] = value.split()
                elif isinstance(value, list):
                    normalized_attrs[key] = value
            else:
                normalized_attrs[key] = value
        return normalized_attrs

    def element_matches(self, lxml_element, bs_element):
        lxml_attribs = self.normalize_attributes(lxml_element.attrib)
        bs_attribs = self.normalize_attributes(bs_element.attrs)

        return lxml_element.tag == bs_element.name and lxml_attribs == bs_attribs


class RobulaPlus:
    def __init__(self, options=None):
        if options:
            self.attribute_priorization_list = options.attribute_priorization_list
            self.attribute_black_list = options.attribute_black_list
        else:
            self.attribute_priorization_list = ['name', 'class', 'title', 'alt', 'value']
            self.attribute_black_list = [
                'href',
                'src',
                'onclick',
                'onload',
                'tabindex',
                'width',
                'height',
                'style',
                'size',
                'maxlength',
            ]

    @timeout_decorator(300)
    def get_robust_xpath(self, element, document):
        if not self.element_in_document(element, document):
            raise ValueError('Document does not contain given element!')

        xpath_list = [XPath('//*')]
        while xpath_list:
            xpath = xpath_list.pop(0)
            temp = []
            try:
                ancestor = self.get_ancestor(element, xpath.get_length() - 1)
                if ancestor.name == '[document]':  #AttributeError: 'NoneType' object has no attribute 'name'
                    continue
            except AttributeError as e:
                continue
            temp.extend(self.transf_convert_star(xpath, element))
            temp.extend(self.transf_add_id(xpath, element))
            temp.extend(self.transf_add_text(xpath, element))
            temp.extend(self.transf_add_attribute(xpath, element))
            temp.extend(self.transf_add_attribute_set(xpath, element))
            temp.extend(self.transf_add_position(xpath, element))
            temp.extend(self.transf_add_level(xpath, element))
            temp = list(set(temp))  # removes duplicates
            for x in temp:
                if self.uniquely_locate(x.get_value(), element, document):
                    return x.get_value()
                xpath_list.append(x)
            if len(xpath_list)>5000:
                return None
        raise ValueError('Internal Error: xPathList.pop returns undefined')

    def get_element_by_xpath(self, xpath, document):
        tree = etree.HTML(str(document))
        elements = tree.xpath(xpath)
        if elements:
            return elements[0]
        return None

    def uniquely_locate(self, xpath, element, document):
        tree = etree.HTML(str(document))
        try:
            elements = tree.xpath(xpath)
            return len(elements) == 1 and self.element_matches(elements[0], element)
        except (XPathSyntaxError, XPathEvalError) as e:
            return False

    def element_matches(self, lxml_element, bs_element):
        comparer = ElementComparer()
        result = comparer.element_matches(lxml_element, bs_element)
        return lxml_element.tag == bs_element.name and result

    def transf_convert_star(self, xpath, element):
        output = []
        ancestor = self.get_ancestor(element, xpath.get_length() - 1)
        if ancestor.name == '[document]':
            return output
        if xpath.starts_with('//*'):
            output.append(XPath('//' + ancestor.name + xpath.substring(3)))
        return output

    def transf_add_id(self, xpath, element):
        output = []
        ancestor = self.get_ancestor(element, xpath.get_length() - 1)
        if 'id' in ancestor.attrs and not xpath.head_has_any_predicates():
            new_xpath = XPath(xpath.get_value())
            new_xpath.add_predicate_to_head(f"[@id='{ancestor.attrs['id']}']")
            output.append(new_xpath)
        if ancestor.name == '[document]':
            return output
        return output

    def transf_add_text(self, xpath, element):
        output = []
        ancestor = self.get_ancestor(element, xpath.get_length() - 1)
        if ancestor.text and not xpath.head_has_position_predicate() and not xpath.head_has_text_predicate():
            new_xpath = XPath(xpath.get_value())
            new_xpath.add_predicate_to_head(f"[contains(text(),'{ancestor.text.strip()}')]")
            output.append(new_xpath)
        if ancestor.name == '[document]':
            return output
        return output

    def transf_add_attribute(self, xpath, element):
        output = []
        ancestor = self.get_ancestor(element, xpath.get_length() - 1)
        if not xpath.head_has_any_predicates():
            for priority_attribute in self.attribute_priorization_list:
                if priority_attribute in ancestor.attrs:
                    new_xpath = XPath(xpath.get_value())
                    new_xpath.add_predicate_to_head(
                        f"[@{priority_attribute}='{ancestor.attrs[priority_attribute][0]}']")
                    output.append(new_xpath)
                    break
            for attribute in ancestor.attrs:
                if attribute == "data-url":
                    continue
                if attribute not in self.attribute_black_list and attribute not in self.attribute_priorization_list:
                    new_xpath = XPath(xpath.get_value())
                    new_xpath.add_predicate_to_head(f"[@{attribute}='{ancestor.attrs[attribute]}']")
                    output.append(new_xpath)
        if ancestor.name == '[document]':
            return output
        return output

    def transf_add_attribute_set(self, xpath, element):
        output = []
        ancestor = self.get_ancestor(element, xpath.get_length() - 1)

        if not xpath.head_has_any_predicates():
            self.attribute_priorization_list.insert(0, 'id')
            attributes = {key: value for key, value in ancestor.attrs.items() if key not in self.attribute_black_list}
            attribute_power_set = self.generate_power_set(attributes.items())
            attribute_power_set = [s for s in attribute_power_set if len(s) >= 2]
            attribute_power_set = sorted(attribute_power_set, key=lambda s: (
                len(s),
                [self.attribute_priorization_list.index(a[0]) for a in s if a[0] in self.attribute_priorization_list]))
            self.attribute_priorization_list.pop(0)

            for attribute_set in attribute_power_set:
                predicates = []
                for attr_name, attr_value in attribute_set:
                    if attr_name == 'class':
                        if isinstance(attr_value, str):
                            # Handle the class attribute properly even if it's a single string
                            classes = attr_value.split()
                            for cls in classes:
                                predicates.append(f"contains(concat(' ', normalize-space(@class), ' '), ' {cls} ')")
                    elif attr_name == 'data-url':
                        continue
                    elif attr_value:  # Ensure attr_value is not empty or None
                        # Handle other attributes normally
                        predicates.append(f"@{attr_name}='{attr_value}'")

                if predicates:
                    predicate = f"[{' and '.join(predicates)}]"
                    new_xpath = XPath(xpath.get_value())
                    new_xpath.add_predicate_to_head(predicate)
                    output.append(new_xpath)

        if ancestor.name == '[document]':
            return output
        return output

    def transf_add_position(self, xpath, element):
        output = []
        ancestor = self.get_ancestor(element, xpath.get_length() - 1)
        if not xpath.head_has_position_predicate():
            position = 1
            if xpath.starts_with('//*'):
                position = len(list(ancestor.previous_siblings)) + 1
            else:
                for sibling in ancestor.previous_siblings:
                    if sibling.name == ancestor.name:
                        position += 1
            new_xpath = XPath(xpath.get_value())
            new_xpath.add_predicate_to_head(f"[{position}]")
            output.append(new_xpath)
        if ancestor.name == '[document]':
            return output
        return output

    def transf_add_level(self, xpath, element):
        output = []
        if xpath.get_length() - 1 < self.get_ancestor_count(element):
            output.append(XPath('//*' + xpath.substring(1)))
        return output

    def generate_power_set(self, input):
        return list(chain.from_iterable(combinations(input, r) for r in range(len(input) + 1)))

    def element_in_document(self, element, document):
        return element in document.find_all()

    def get_ancestor(self, element, index):
        output = element
        for _ in range(index):
            output = output.parent
        return output

    def get_ancestor_count(self, element):
        count = 0
        while element.parent:
            element = element.parent
            count += 1
        return count

# Example usage

def get_random_element(website: str):
    soup = BeautifulSoup(website, 'html.parser')
    extract_elements = soup.find_all()
    exclude_tags = ["a", "body", "html", "link", "meta", "script", "head"]
    filtered_elements = [element for element in extract_elements if element.name not in exclude_tags]
    element = random.sample(filtered_elements, 1)
    return element[0]

if __name__ == "__main__":
    path_to_html = "Medium.html"

    with open(path_to_html, 'r', encoding='utf-8') as file:
        website = file.read()
    target_element = get_random_element(website)
    soup = BeautifulSoup(website, 'lxml')
    robula_plus = RobulaPlus()
    try:
        robust_xpath = robula_plus.get_robust_xpath(target_element, soup)
        print(f'Generated XPath: {robust_xpath}')
    except ValueError as e:
        print(e)
