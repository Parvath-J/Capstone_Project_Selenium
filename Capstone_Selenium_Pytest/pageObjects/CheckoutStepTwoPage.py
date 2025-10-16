# pageObjects/CheckoutStepTwoPage.py
from selenium.webdriver.common.by import By
from pageObjects.BasePage import BasePage


class CheckoutStepTwoPage(BasePage):
    # Locators
    TOTAL_LABEL = (By.CSS_SELECTOR, ".summary_info_label.summary_total_label")

    def __init__(self, driver):
        super().__init__(driver)

    def get_total_price(self):
        return self.get_element_text(self.TOTAL_LABEL)

    def click_finish(self):
        self.do_click(self.FINISH_BUTTON)