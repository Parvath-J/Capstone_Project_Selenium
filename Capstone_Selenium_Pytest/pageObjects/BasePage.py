# pageObjects/BasePage.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def do_click(self, by_locator):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(by_locator)).click()

    def do_js_click(self, by_locator):
        element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(by_locator))
        self.driver.execute_script("arguments[0].click();", element)

    def do_send_keys(self, by_locator, text):
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(by_locator)).send_keys(text)

    # THIS IS THE NEW, MORE RELIABLE METHOD FOR TYPING
    def do_robust_send_keys(self, by_locator, text):
        """A more human-like and reliable method for sending keys."""
        element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(by_locator))
        element.click()
        element.clear()
        element.send_keys(text)

    def get_element_text(self, by_locator):
        element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(by_locator))
        return element.text

    def is_visible(self, by_locator):
        try:
            element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(by_locator))
            return element.is_displayed()
        except:
            return False

    def get_title(self, title):
        WebDriverWait(self.driver, 10).until(EC.title_is(title))
        return self.driver.title

    def select_dropdown_by_visible_text(self, by_locator, text):
        dropdown = Select(WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located(by_locator)))
        dropdown.select_by_visible_text(text)