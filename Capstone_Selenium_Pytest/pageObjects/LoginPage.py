# pageObjects/LoginPage.py
from selenium.webdriver.common.by import By
from pageObjects.BasePage import BasePage


class LoginPage(BasePage):
    # Locators
    USERNAME_INPUT = (By.ID, "user-name")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-button")
    ERROR_MESSAGE_LABEL = (By.CSS_SELECTOR, "h3[data-test='error']")

    def __init__(self, driver):
        super().__init__(driver)

    def set_username(self, username):
        self.do_send_keys(self.USERNAME_INPUT, username)

    def set_password(self, password):
        self.do_send_keys(self.PASSWORD_INPUT, password)

    def click_login(self):
        self.do_click(self.LOGIN_BUTTON)

    def get_error_message(self):
        if self.is_visible(self.ERROR_MESSAGE_LABEL):
            return self.get_element_text(self.ERROR_MESSAGE_LABEL)
        return "No error message found."