import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

import itertools


def generate_locator_relative(element):
    xpath_string = "/"
    xpath_list = []
    current_element = element
    while "id" not in current_element.attrs:
        position, flag = get_siblings_soup(current_element, True)
        if flag:
            xpath_list.append((current_element, position))
        else:
            xpath_list.append((current_element, -1))
        current_element = current_element.parent
        try:
            if current_element.name == "html":
                xpath_string += '/' + current_element.name
                break
        except:
            break
    try:
        if current_element.name != "html":
            xpath_string += '/*[@id="' + current_element.attrs["id"] + '"]'
    except:
        print("nonetype")
    for path_element in reversed(xpath_list):
        if path_element[1] == -1:
            xpath_string += "/" + path_element[0].name
        else:
            xpath_string += "/" + path_element[0].name + '[' + str(path_element[1]) + ']'
    return xpath_string

def get_siblings_soup(soup, cal_pos=False):
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

def generate_fullxpath(element):
    xpath_string = "/"
    xpath_list = []
    current_element = element
    while current_element.name != "html":
        position, flag = get_siblings_soup(current_element, True)
        if flag:
            xpath_list.append((current_element, position))
        else:
            xpath_list.append((current_element, -1))
        current_element = current_element.parent
        try:
            if current_element.name == "html":
                xpath_string += '/' + current_element.name
                break
        except:
            break
    for path_element in reversed(xpath_list):
        if path_element[1] == -1:
            xpath_string += "/" + path_element[0].name
        else:
            xpath_string += "/" + path_element[0].name + '[' + str(path_element[1]) + ']'
    return xpath_string

def generate_selenium_locator(element):
    tag = element.name

    # Get all the attributes of the element
    attributes = element.attrs
    locators = []

    for attribute in attributes:
        # Get the attribute value
        attribute_value = attributes[attribute]
        # Generate a random locator based on the selected attribute
        if attribute == 'class':
            if attribute_value:
                locators.append((By.CLASS_NAME, attribute_value))
        if attribute == 'id':
            locators.append((By.ID, attribute_value))
        if attribute == 'name':
            locators.append((By.NAME, attribute_value))
        if attribute == 'href':
            locators.append((By.LINK_TEXT, attribute_value))
        # locators.append((By.CSS_SELECTOR, f'{tag}[{attribute}="{attribute_value}"]'))
    locators.append((By.XPATH, generate_fullxpath(element)))
    locators.append((By.XPATH, generate_locator_relative(element)))
    return locators

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
    print(target_element)
    try:
        locators = generate_selenium_locator(target_element)
        for locator in locators:
            print(f'Locator Type: {locator[0]}, Value: {locator[1]}')
    except ValueError as e:
        print(e)
