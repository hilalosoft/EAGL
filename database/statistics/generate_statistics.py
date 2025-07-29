import os
import random
import pandas as pd
from bs4 import BeautifulSoup
# from Classes.PredictionClass import PredictionClass
import database.statistics.graphics as graphics
import Classes.soup_operations as so
import Classes.PredictionClass as PC


# from Classes.Database_class import get_websites, get_history


def generate_statistics_from_dom(dom, timestamp):
    parsed_dom = BeautifulSoup(dom, 'html.parser')
    tag_dictionary = {}
    depth_list = []
    tag_list = []
    count_tags = 0
    # PC = PredictionClass(parsed_dom)

    for child in parsed_dom.descendants:
        if child.name is None:
            continue
        elif "id" in child.attrs and child['id'] == "wm-ipp":
            del child
            continue
        count_tags += 1
        position, siblings = so.get_siblings_soup(child)
        depth_list.append((child.name, so.cal_length(child, max_depth), so.xpath_soup(child), position, siblings))
        if child.name in tag_dictionary:
            tag_dictionary[child.name] += 1
        else:
            tag_dictionary[child.name] = 1
    for key in tag_dictionary:
        tag_list.append((key, tag_dictionary[key]))

    df_tags = pd.DataFrame(tag_list)
    df_depth = pd.DataFrame(depth_list)
    # if not os.path.isfile('list.csv'):
    df_tags.to_csv('data/list_' + str(timestamp) + '.csv', header=["tag", "Occurrences"], index=False)
    df_depth.to_csv('data/tag_list_' + str(timestamp) + '.csv',
                    header=["tag", "depth", "xpath", "position", "siblings"],
                    index=False)
    # else:
    #     df_tags.to_csv('list.csv', mode='a', header=None, index=False)
    #     df_depth.to_csv('tag_list.csv', mode='a', header=None, index=False)

    df = pd.read_csv('data/list_' + str(timestamp) + '.csv')
    graphics.boxplot(df, "tag_list_" + str(timestamp), x='Occurrences', y="tag")


def generate_graphics_dom_list(dom_list, project_name):
    tag_dictionary = {}
    none_tag = "string"
    index = 1
    feature_vectors = []
    for dom in dom_list:
        dom_dictionary = {}
        count_tags = 0
        parsed_dom = BeautifulSoup(dom, 'html.parser')
        max_depth = so.cal_max_length(parsed_dom)
        for child in parsed_dom.descendants:
            if str(type(child)) == "<class 'bs4.element.Script'>" or str(type(child)) == "<class 'bs4.element" \
                                                                                         ".Stylesheet'>" or str(
                type(child)) == "<class 'bs4.element.Comment'>" or str(
                type(child)) == "<class 'bs4.element.Declaration'>" or str(
                type(child)) == "<class 'bs4.element.TemplateString'>" or str(
                type(child)) == "<class 'bs4.element.typetext'>" or str(
                type(child)) == "<class 'bs4.element.Doctype'>":
                continue
            count_tags += 1
            if str(type(child)) == "<class 'bs4.element.NavigableString'>":
                # vector_array.append((none_tag, so.cal_depth(child), so.xpath_soup(child)))
                if none_tag in dom_dictionary:
                    dom_dictionary[none_tag] += 1
                else:
                    dom_dictionary[none_tag] = 1
            elif "id" in child.attrs and child['id'] == "wm-ipp":
                del child
                continue
            else:
                if child.name == "script":
                    continue
                feature_vectors.append(so.generate_vectors_from_soup(child, max_depth))
                if child.name in dom_dictionary:
                    dom_dictionary[child.name] += 1
                else:
                    dom_dictionary[child.name] = 1
        dom_dictionary['number_of_tags'] = count_tags
        for key in dom_dictionary:
            if key in tag_dictionary:
                tag_dictionary[key].append((index, dom_dictionary[key]))
            else:
                tag_dictionary[key] = []
                tag_dictionary[key].append((index, dom_dictionary[key]))
        index += 1

    # create_feature_csv(feature_vectors, project_name)

    # header = []
    # tag_list = [[0 for x in range(0, len(tag_dictionary))] for y in range(0, 1000)]
    # tag_indexes = {}
    # counter = 0
    # for key in tag_dictionary:
    #     header.append(key)
    #     tag_indexes[key] = counter
    #     counter += 1
    # for i in range(0, 1000):
    #     for key in tag_dictionary:
    #         for index_array in tag_dictionary[key]:
    #             if index_array[0] == i:
    #                 tag_list[i][tag_indexes[key]] = index_array[1]
    #                 continue
    #
    # df_tags = pd.DataFrame(tag_list)
    # df_tags.to_csv('data/list_' + str(project_name) + '.csv', header=header, index=False)

    # graphics.violinplot(df_tags, "tag_list_", x='Occurrences', y="tag")


def preprocess_dom_locators(dom, model_name,scaled):
    soup = BeautifulSoup(dom, 'html.parser')
    extract_elements = soup.find_all()
    exclude_tags = ["a","body","html","link","meta","script","head"]

    # Use a list comprehension to filter out excluded tags
    filtered_elements = [element for element in extract_elements if element.name not in exclude_tags]

    if len(filtered_elements) >= 20:
        elements = random.sample(filtered_elements, 20)
    elif len(filtered_elements) >= 30:
        elements = random.sample(filtered_elements, len(filtered_elements))
    else:
        return [], [], 0, 0, len(extract_elements)
    locators_RELOC, time_RELOC = PC.generate_locators_prediction_model(soup, elements, model_name,scaled)
    locators_relative_xpath, time_SEL = so.generate_locators_relative_xpath(elements)
    locators_robula, time_robula = so.generate_locators_robulaplus(elements)
    assert len(locators_RELOC) == len(locators_relative_xpath), f"{len(locators_RELOC)},{len(locators_robula)}"
    # locators_relative_xpath = PC.generate_locators_xpath(elements)
    # num_of_elements= len(soup)
    return locators_RELOC, locators_relative_xpath, time_RELOC, time_SEL,locators_robula,time_robula,len(extract_elements)


def process(project_history):
    dom_list = []
    timestamp_list = []
    fc = so.featureClass()
    project_name = project_history[0][3]
    project_history.sort(key=lambda x: x[7])
    print("processing " + project_name)
    for row in project_history:
        # generate_statistics_from_dom(row[1], row[7])
        dom_list.append(row[1])
        timestamp_list.append(row[7])
    if len(dom_list) > 2:
        fc.generate_feature_vector_dom(dom_list, timestamp_list, project_name)
    # print(str(len(dom_list)) + " doms out of from " + str(len(project_history)))
    # generate_graphics_dom_list(dom_list, project_name)

# def process_from_database():
#     websites = get_websites()
#     dom_list = []
#     for website in websites:
#         website_history = get_history(website)
#         for version in website_history:
#             dom_list.append(version[0])
#         generate_graphics_dom_list(dom_list, website)
