# pageObjects/CartPage.py
from selenium.webdriver.common.by import By
from pageObjects.BasePage import BasePage


class CartPage(BasePage):
    # Locators
    CHECKOUT_BUTTON = (By.ID, "checkout")
    ITEM_NAME_LINK = (By.ID, "item_4_title_link")  # Specific to backpack

    def __init__(self, driver):
        super().__init__(driver)

    def is_item_in_cart(self):
        return self.is_visible(self.ITEM_NAME_LINK)

    def click_checkout(self):
        self.do_click(self.CHECKOUT_BUTTON)