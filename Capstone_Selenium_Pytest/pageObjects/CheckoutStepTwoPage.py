# pageObjects/CheckoutStepTwoPage.py
from selenium.webdriver.common.by import By
from pageObjects.BasePage import BasePage


class CheckoutStepTwoPage(BasePage):
    # This is the corrected locator for the total price element
    TOTAL_LABEL = (By.CSS_SELECTOR, ".summary_total_label")
    FINISH_BUTTON = (By.ID, "finish")

    def __init__(self, driver):
        super().__init__(driver)

    def get_total_price(self):
        # This method will now find the element correctly
        return self.get_element_text(self.TOTAL_LABEL)

    def click_finish(self):
        self.do_click(self.FINISH_BUTTON)