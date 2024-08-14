import pandas as pd
import requests
from Classes.DOM_class import DOMClass, set_project, add_dom
# from Classes.Database_class import connect_to_db


def query_page_info(project_name, website, lowerbound=0, upperbound=1):
    if DOMClass.current_project != project_name:
        set_project(project_name)

    versions = request_history(website)
    if not versions:
        return False

    count = 0
    list_urls = []
    list_timestamps = []
    last_timestamp = "0"
    try:
        for i in range(lowerbound + 2, len(versions)):
            if count >= upperbound:
                break
            url, timestamp = retrieve_url_timestamp(versions[i])

            if last_timestamp == "0":
                last_timestamp = timestamp
            elif float(last_timestamp[:8]) <= float(timestamp[:8]):
                continue
            if request_and_save_page(url, website, timestamp) is False:
                continue
            last_timestamp = timestamp
            list_urls.append(url)
            list_timestamps.append(timestamp)
            count = count + 1
        print("Collected "+str(len(list_urls))+" history versions")
        padnas_dict = {'websitelink': list_urls, 'timestamp': list_timestamps}
        df = pd.DataFrame(padnas_dict)
        df.to_csv('database/websites/weblinks_' + project_name + '.csv')
        connect_to_db()
        return True
    except Exception as e:
        if count >= 1000:
            padnas_dict = {'websitelink': list_urls, 'timestamp': list_timestamps}
            df = pd.DataFrame(padnas_dict)
            df.to_csv('database/websites/weblinks_' + project_name + '.csv')
            connect_to_db()
            return True
        else:
            return False


def query_page_info_continue(project_name, website, lowerbound=0, upperbound=1, previous_timestamp=None):
    if DOMClass.current_project != project_name:
        set_project(project_name)
    versions = request_history(website)
    list_urls = []
    list_timestamps = []
    count = 0
    for i in range(lowerbound + 2, len(versions)):
        if count >= upperbound:
            break
        url, timestamp = retrieve_url_timestamp(versions[i])
        if float(timestamp) >= float(previous_timestamp):
            continue
        request_and_save_page(url, website, timestamp)
        list_urls.append(url)
        list_timestamps.append(timestamp)
        count = count + 1

    padnas_dict = {'websitelink': list_urls, 'timestamp': list_timestamps}
    df = pd.DataFrame(padnas_dict)
    df.to_csv('database/websites/weblinks_' + project_name + '.csv')
    connect_to_db()
    return


def request_history(website):
    url = extract_url(website)
    response = requests.get(url, stream=True, timeout=1000)
    if response.status_code != 200:
        print("error retrieving history data")
        return False
    versions = response.text.split('\n ')
    versions.reverse()
    return versions


def extract_url(website):
    if len(website) < 10 or website[10:] != "http://www.":
        website = "http://www." + website
    url = 'https://timetravel.mementoweb.org/timemap/link/' + website
    return url


def retrieve_url_timestamp(version):
    split_version = version.split(';')
    version_url = split_version[0]  # extract the url of the website only from the response
    times = split_version[2].split(' ')  # extract the url of the website only from the response
    timestamp = times[4] + mtn(times[3]) + times[2] + times[5].replace(':', '')
    version_url = version_url[1:len(version_url) - 2]
    return version_url, timestamp


def request_and_save_page(url, website, timestamp):
    try:
        print(url)
        response = requests.get(url)
        obj_dom = DOMClass(website, timestamp, response.text)
        add_dom(obj_dom)
        return True
    except Exception as error:
        print('page skipped, {0}'.format(error))
        return False


def mtn(x):
    months = {
        'jan': '01',
        'feb': '02',
        'mar': '03',
        'apr': '04',
        'may': '05',
        'jun': '06',
        'jul': '07',
        'aug': '08',
        'sep': '09',
        'oct': '10',
        'nov': '11',
        'dec': '12'
    }
    a = x.strip()[:3].lower()
    try:
        ez = months[a]
        return ez
    except:
        raise ValueError('Not a month')
