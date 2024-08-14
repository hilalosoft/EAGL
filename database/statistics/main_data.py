import os
import pandas as pd
from bs4 import BeautifulSoup
import generate_statistics

from Classes.Database_class import query_from_db
from Classes.DriverClass import DriverObject
from database.statistics import graphics
import csv

faulty_list = ["wsj", "slickdeals", "yahoo"]


def main():
    projects = query_from_db()
    file_list_old = os.listdir(os.getcwd() + "\data\scaled")
    file_list_hpc = os.listdir("C:\\Users\\hilal.taha\\Desktop\\data\\scaled")
    newfile_list = []
    for file in file_list_old + file_list_hpc:
        newfile_list.append(file[13:len(file) - 4])
    for project in projects:
        if project[0] + "_scaled" in newfile_list:
            print(project)
            continue
        if project[0] in faulty_list:
            continue
        # project[0]
        entire_history = query_from_db("select * from dom where project = '" + project[0] + "';")
        generate_statistics.process(entire_history)

    # filename = "filename.csv"
    # chunksize = 1000
    # count = 0
    # # get_websites
    # with pd.read_csv(filename, chunksize=chunksize) as reader:
    #     for chunk in reader:
    #         count += 1
    #         generate_statistics.process(chunk)
    #         continue
    #     print('chunk number: ' + str(count))
    # generate_statistics.process_from_database()


def categorize_websites(training_model):
    if scaled:
        project_name = training_model[:len(training_model) - 14]
        if training_model[:len(training_model) - 14] + ".csv" in os.listdir(
                os.getcwd() + "./evaluation_data/"):
            print("skipping " + project_name)
            return
    else:
        project_name = training_model[:len(training_model) - 7]
        if training_model[:len(training_model) - 7] + ".csv" in os.listdir(
                os.getcwd() + "./evaluation_data/None_scaled/"):
            print("skipping " + project_name)
            return


def generate_graphics():
    filename = os.getcwd() + "\\data\\feature_list_1688.csv"
    df = pd.read_csv(filename, delimiter=",")
    graphics.lineplot(df, "feature_list_1688", x=df.timestamp.apply(lambda f: pd.to_datetime(str(f))),
                      y=df['changed'])
    # graphics.lineplot(df, "feature_list_1337x", x=df["position"], y=df['changed'])
    # for column in list(df.columns):
    #     # graphics.lineplot(df, "tags_apple" + str(colum), x=df.index, y=column)
    #     graphics.lineplot(df, "facebook_" + "number_of_tags", x=df.index, y=column)
    # graphics.violinplot(df, "tags", x=df.index, y='string')
    # graphics.countplot(df, "tags", x='string')


scaled = True


def retrieve_history(project_name):
    dom_list=[]
    timestamps=[]
    index=1
    faulty_list1 = ["naukri", "wordre", "163"]
    if project_name in faulty_list1:
        return None,0
    print("getting history:" + project_name)
    csv_file_path = "./evaluation_data/" +project_name+'.csv'
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        # Iterate over each row in the CSV file
        for row in reader:
            # Append the value from the 'Timestamp' column to the list
            timestamps.append(row['Timestamp'])
    # Assuming 'timestamps' is your list of timestamps
    formatted_timestamps = ', '.join(f"'{timestamp}'" for timestamp in timestamps)
    query = f"""
        SELECT * FROM dom 
        WHERE project = '{project_name}' 
        AND "time" IN ({formatted_timestamps});
    """
    entire_history = query_from_db(query)
    index=len(entire_history)
    if entire_history == []:
        query = f"""
                SELECT * FROM dom 
                WHERE project = '{project_name}';
            """
        entire_history = query_from_db(query)
        index=int(len(entire_history)/5)
    print("history retrieved")
    for row in entire_history:
        dom_list.append((row[7], row[1]))
    dom_list.sort()
    return dom_list,index

def generate_and_test_locators_for_DOM(training_model):
    if scaled:
        project_name = training_model[:len(training_model) - 14]
        if project_name + "_located.csv" in os.listdir(
                os.getcwd() + "./evaluation_data/revision/"):
            print("skipping " + project_name)
            return
    else:
        project_name = training_model[:len(training_model) - 7]
        if training_model[:len(training_model) - 7] + ".csv" in os.listdir(
                os.getcwd() + "./evaluation_data/None_scaled/"):
            print("skipping " + project_name)
            return

    dom_list,index = retrieve_history(project_name)
    if dom_list is None:
        return
    # index = len(dom_list)
    # index = int(len(dom_list) / 5)

    locators_RELOC = None
    try:
        locators_RELOC, locators_Selenium, timeRELOC, timeSEL, locators_robula, time_robula, number_of_elements = (
            generate_statistics.preprocess_dom_locators(dom_list[len(dom_list) - index][1], project_name, scaled))
    except Exception as e:
        print(e)
    while not locators_RELOC or number_of_elements < 30:
        index += 1
        try:
            locators_RELOC, locators_Selenium, timeRELOC, timeSEL, locators_robula, time_robula, number_of_elements = (
                generate_statistics.preprocess_dom_locators(dom_list[len(dom_list) - index][1], project_name, scaled))
        except Exception as e:
            print(e)

    assert (len(locators_RELOC) > 19)
    df_time_to_compute = pd.DataFrame({'timeRELOC': timeRELOC, 'timeSEL': timeSEL, 'timeRobula': time_robula})
    df_time_to_compute.to_csv('./evaluation_data/revision/locators_generation_' + project_name + '.csv',
                              encoding='utf-8', mode="w", header=True)

    locators_statistics, locators_num_located, skipped_doms = [], [], []
    last_locators_RELOC, last_locators_SEL = 0, 0
    DC = DriverObject()
    for i in range(len(dom_list) - index, len(dom_list), 1):  # len(dom_list) - int(len(dom_list) / 5)
        print(dom_list[i][0])
        try:
            DC.get_page(dom_list[i][1])
            soup = BeautifulSoup(dom_list[i][1], 'html.parser')
            soup_body = soup.find("body")
            extract_elements = soup_body.find_all()
        except Exception as e:
            skipped_doms.append(dom_list[i][0])
            print("Error:", e)
            continue
        if not soup_body and len(extract_elements) <= 20:
            skipped_doms.append(dom_list[i][0])
            print("skipped")
            continue
        count_true_selenium, count_selenium_locators, count_true_prediction, count_true_robula = 0, 0, 0, 0
        element_dict = {"Timestamp": dom_list[i][0]}
        dict_num_located = {"Timestamp": dom_list[i][0]}

        for j in range(0, len(locators_RELOC), 1):
            located, RELOC_num_located = DC.test_locator(locators_RELOC[j])
            # element_dict[locators_RELOC[j] + "_RELOC"] = located
            dict_num_located[locators_RELOC[j] + "_RELOC"] = RELOC_num_located
            if located:
                count_true_prediction += 1

            located, robula_num_located = DC.test_locator(locators_robula[j])
            dict_num_located[str(locators_robula[j]) + "_ROBULA"] = robula_num_located
            if located:
                count_true_robula += 1

            if robula_num_located != RELOC_num_located:
                print("manual check RELOC locator " + locators_RELOC[j] + " vs Robula plus locator:" + str(
                    locators_robula[j]))

            for selenium_locator in locators_Selenium[j]:
                count_selenium_locators += 1
                located, selenium_num_located = DC.test_locators_selenium(selenium_locator[0], selenium_locator[1])
                if selenium_num_located > 1:
                    located = False
                if selenium_locator[0] == "class name":
                    element_dict[selenium_locator[0] + selenium_locator[1][0] + "_SEL"] = located
                    dict_num_located[selenium_locator[0] + selenium_locator[1][0] + "_SEL"] = selenium_num_located
                else:
                    element_dict[selenium_locator[0] + selenium_locator[1] + "_SEL"] = located
                    dict_num_located[selenium_locator[0] + selenium_locator[1] + "_SEL"] = selenium_num_located
                if located:
                    count_true_selenium += 1
        # locators_statistics.append(element_dict)
        locators_num_located.append(dict_num_located)

        print(str(count_true_prediction) + ": Survived from EAGL out of " + str(len(locators_RELOC)))
        print(str(count_true_robula) + ": Survived from Robula out of " + str(len(locators_RELOC)))
        print(str(count_true_selenium) + ": Survived from Selenium out of " + str(count_selenium_locators))
    DC.close()
    if not scaled:
        df = pd.DataFrame(locators_statistics)
        if len(df) < 1:
            return
        df.to_csv('./evaluation_data/None_scaled/' + project_name + '.csv', mode='a')
        df = pd.DataFrame(locators_num_located)
        df.to_csv('./evaluation_data/None_scaled/' + project_name + '_located.csv', mode='a')
        df = pd.DataFrame(skipped_doms)
        df.to_csv('./evaluation_data/None_scaled/' + project_name + '_skipped.csv', mode='a')
    else:
        # df = pd.DataFrame(locators_statistics)
        df = pd.DataFrame(locators_num_located)
        if len(df) <= 1:
            return
        # df.to_csv('./evaluation_data/revision/' + project_name + '.csv', mode='a')
        df.to_csv('./evaluation_data/revision/' + project_name + '_located.csv', mode='a')
        df = pd.DataFrame(skipped_doms)
        df.to_csv('./evaluation_data/revision/' + project_name + '_skipped.csv', mode='a')


def process_excel_files(directory):
    # Get a list of all files in the directory that end with "_located.csv"
    files = [f for f in os.listdir(directory) if f.endswith("_located.csv")]
    locating_strategies = ["id", "name", "class name", "tag name", "xpath", "link text", "partial link text",
                           "css selector"]
    for file in files:
        # Construct the full path to the file
        file_path = os.path.join(directory, file)

        locators_Selenium = []
        locators_RELOC = []
        # Read the Excel file into a DataFrame
        df = pd.read_csv(file_path)

        # Get the header (first row) as a list
        header = df.columns.tolist()

        for i in range(2, len(header)):
            flag = False
            locator_value = header[i]
            for loc_strategy in locating_strategies:
                if locator_value.startswith(loc_strategy):
                    locator_value = locator_value[len(loc_strategy):-4]
                    locators_Selenium.append((loc_strategy, locator_value))
                    flag = True
            if flag:
                continue
            locators_RELOC.append(locator_value[:-6])
        project_name = file[:-12]

        # print(project_name,len(locators_RELOC))

        dom_list = []
        print("getting history:" + project_name)
        entire_history = query_from_db("select * from dom where project = '" + project_name + "';")
        print("history retrieved")
        for row in entire_history:
            dom_list.append((row[7], row[1]))
        dom_list.sort()
        index = int(len(dom_list) / 5)
        DC = DriverObject()

        try:
            _, _, _, _, _, _, number_of_elements = generate_statistics.preprocess_dom_locators(
                dom_list[len(dom_list) - index][1], project_name, scaled)
        except Exception as e:
            print(e)
        while not locators_RELOC or number_of_elements < 30:
            index += 1
            try:
                _, _, _, _, _, _, number_of_elements = generate_statistics.preprocess_dom_locators(
                    dom_list[len(dom_list) - index][1], project_name, scaled)
            except Exception as e:
                print(e)
        try:
            DC.get_page(dom_list[len(dom_list) - index][1])
        except Exception as e:
            print("Error:", e)
            continue
        dict_num_located = {"Timestamp": dom_list[len(dom_list) - index][0]}
        for j in range(0, len(locators_RELOC), 1):
            located, num_located = DC.test_locator(locators_RELOC[j])
            dict_num_located[locators_RELOC[j] + "_RELOC"] = num_located
        for j in range(0, len(locators_Selenium), 1):
            located, num_located = DC.test_locators_selenium(locators_Selenium[j][0], locators_Selenium[j][1])
            dict_num_located[locators_Selenium[j][0] + locators_Selenium[j][1] + "_SEL"] = num_located

        new_row = pd.DataFrame(dict_num_located, index=[0])
        df = pd.concat([new_row, df]).reset_index(drop=True)
        # Replace 'your_file.csv' with the path to your CSV file
        df.to_csv('your_file.csv', index=False)

        # Save the modified DataFrame back to the Excel file
        # df.to_excel("processed_"+file_path, index=False)


# process_excel_files(os.getcwd()+"/evaluation_data/")

for model in os.listdir("C:/Users/hilal.taha/Desktop/data/models/scaled"):
    if model == "None_scaled" or model == "Pickles":
        continue
    generate_and_test_locators_for_DOM(model)
# generate_and_test_locators_for_DOM("wordpress")
# generate_graphics()
# retrieve_dom_generate_locators()
# main()
# entire_history = query_from_db("select * from dom where project = '17ok';")
# for history in entire_history:
#     if history[7]=='20191030005941':
#         print(history)
