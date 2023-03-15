import typing
import urllib.parse

import selenium.webdriver
from selenium.webdriver.common.by import By


class Site:
    def __init__(self, driver: selenium.webdriver.Chrome, base_url: str):
        self._driver = driver
        self._base_url = base_url

    def go_to(self, path: str = None):
        url = self._base_url if path is None else f"{self._base_url}?{path}"
        self._driver.get(url)

    def get_field_by_id(self, id):
        return self._driver.find_element(By.ID, id)

    def send_key(self, id: str, key: selenium.webdriver.Keys):
        field = self._driver.find_element(By.ID, id)
        field.send_keys(key)

    def execute_script(self, script: str, *args):
        self._driver.execute_script(script, *args)

    def set_value(self, id: str, text: str):
        self.execute_script(f"document.getElementById('{id}').value = '{text}'")

    def set_first_value_by_type(self, type: str, value: str):
        self.execute_script(f"document.querySelectorAll('[type=\"{type}\"]')[0].value = '{value}'")

    def set_first_value_by_attribute_name_and_value(self, attribute_name: str, attribute_value, value):
        self.execute_script(f"document.querySelectorAll('[{attribute_name}=\"{attribute_value}\"]')[0].value = '{value}'")

    def click_field(self, id: str):
        field = self._driver.find_element(By.ID, id)
        field.click()

    def set_combo_box_value_by_name(self, name, text):
        self.execute_script(f"document.getElementsByName('{name}')[0].value = '{text}'")

    def set_combo_box_value_by_id(self, id, text):
        self.execute_script(f"document.getElementById('{id}').value = '{text}'")

    def submit(self):
        self.execute_script(f"document.querySelectorAll('[type=\"submit\"]')[0].click()")

    def refresh(self):
        self._driver.refresh()

    def get_current_url(self) -> str:
        return self._driver.current_url

    def get_url_parameters(self) -> typing.Dict:
        parsed = urllib.parse.urlparse(self.get_current_url())
        return urllib.parse.parse_qs(parsed.query)
