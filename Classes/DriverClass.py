import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, InvalidSelectorException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# process manager
class DriverObject:
    driver = None
    options = Options()
    filename = "comparing.html"

    def __init__(self, interactable=False):
        if not interactable:
            self.options.add_argument("--disable-javascript")
            self.options.add_argument("start-maximized")
            self.options.add_argument("enable-automation")
            self.options.add_argument("--headless")
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--disable-browser-side-navigation")
            self.options.add_argument('--headless')
            self.options.add_argument('--disable-gpu')
            self.options.add_argument("--disable-network")
            self.options.add_experimental_option('prefs', {'profile.managed_default_content_settings.javascript': 2})
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_page_load_timeout(60)

    def get_page(self, dom):
        textfile = open(os.getcwd() + self.filename, "w", encoding='utf-8')
        textfile.write(dom)
        textfile.close()
        self.driver.get(os.getcwd() + self.filename)
        js = "window.stop();"
        self.driver.execute_script(js)

    def save_page(self, save_path):
        self.driver.save_screenshot(save_path)

    def close(self):
        try:
            self.driver.close()
        except:
            try:
                self.driver.quit()
            except:
                return

    def get_url(self,url):
        self.driver.get(url)
        self.driver.implicitly_wait(100)

    def element_changed(self, xpath, soup, attribute=None, text_content=None):
        try:
            elem = self.driver.find_element(By.XPATH, xpath)
            if attribute:
                if isinstance(text_content, list):
                    attribute_string = ""
                    for value in text_content:
                        attribute_string = attribute_string + value
                else:
                    attribute_string = text_content
                attribute_value = elem.get_attribute(attribute)
                if attribute_value == attribute_string:
                    return False
                else:
                    return True
            if text_content:
                if elem.text == text_content:
                    return False
                else:
                    return True
            if elem.tag_name == soup.name:
                return False
            else:
                return True
        except NoSuchElementException as e:
            return True
        except InvalidSelectorException as e:
            return False

    def test_locator(self, xpath):
        if xpath is None:
            return False, 0
        try:
            elements = self.driver.find_elements(By.XPATH, xpath)
            if len(elements) == 1:
                return True, len(elements)
            elif len(elements) > 1:
                return False, len(elements)
            else:
                return False, len(elements)
        except NoSuchElementException as e:
            return False, 0
        except InvalidSelectorException as e:
            return False, 0

    def test_locators_selenium(self, locator, value):
        try:
            if locator == 'class name':
                for v in value:
                    elements = self.driver.find_elements(locator, v)
                    if len(elements) == 1:
                        return True, len(elements)
                return False, len(elements)
            else:
                elements = self.driver.find_elements(locator, value)
                if len(elements) == 1:
                    return True, len(elements)
                else:
                    return False, len(elements)
        except NoSuchElementException as e:
            return False, 0
        except InvalidSelectorException as e:
            return False, 0
