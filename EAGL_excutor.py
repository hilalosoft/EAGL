import os
import random
from bs4 import BeautifulSoup
import Classes.PredictionClass as PC


def get_random_element(website: str):
    soup = BeautifulSoup(website, 'html.parser')
    extract_elements = soup.find_all()
    exclude_tags = ["a", "body", "html", "link", "meta", "script", "head"]
    filtered_elements = [element for element in extract_elements if element.name not in exclude_tags]
    element = random.sample(filtered_elements, 1)
    return element


if __name__ == "__main__":
    path_to_model = os.getcwd() + "\\database\\cross_training.joblib"
    path_to_html = "Medium.html"

    with open(path_to_html, 'r', encoding='utf-8') as file:
        website = file.read()

    target_element = get_random_element(website)
    try:
        locators, time_to_generate = PC.generate_locators_prediction_model(target_element, path_to_model)
        print(f"Generated Locator:{locators}")
    except ValueError as e:
        print(e)
