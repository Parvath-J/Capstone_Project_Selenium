# pageObjects/CheckoutStepOnePage.py
from selenium.webdriver.common.by import By
from pageObjects.BasePage import BasePage


class CheckoutStepOnePage(BasePage):
    # Locators
    FIRST_NAME_INPUT = (By.ID, "first-name")
    LAST_NAME_INPUT = (By.ID, "last-name")
    POSTAL_CODE_INPUT = (By.ID, "postal-code")
    CONTINUE_BUTTON = (By.ID, "continue")

    def __init__(self, driver):
        super().__init__(driver)

    def enter_checkout_info(self, first_name, last_name, postal_code):
        # USE THE NEW ROBUST METHOD
        self.do_robust_send_keys(self.FIRST_NAME_INPUT, first_name)
        self.do_robust_send_keys(self.LAST_NAME_INPUT, last_name)
        self.do_robust_send_keys(self.POSTAL_CODE_INPUT, postal_code)

    def click_continue(self):
        self.do_click(self.CONTINUE_BUTTON) # A standard click should be fine here