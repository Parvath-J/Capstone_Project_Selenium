# pageObjects/InventoryPage.py
from selenium.webdriver.common.by import By
from pageObjects.BasePage import BasePage


class InventoryPage(BasePage):
    # Locators
    PAGE_TITLE = (By.CLASS_NAME, "title")
    SHOPPING_CART_LINK = (By.CLASS_NAME, "shopping_cart_link")
    ADD_TO_CART_SAUCE_LABS_BACKPACK_BUTTON = (By.ID, "add-to-cart-sauce-labs-backpack")
    SORT_DROPDOWN = (By.CLASS_NAME, "product_sort_container")

    def __init__(self, driver):
        super().__init__(driver)

    def get_page_title(self):
        return self.get_element_text(self.PAGE_TITLE)

    def add_backpack_to_cart(self):
        self.do_click(self.ADD_TO_CART_SAUCE_LABS_BACKPACK_BUTTON)

    def click_shopping_cart(self):
        self.do_click(self.SHOPPING_CART_LINK)

    def sort_products(self, visible_text):
        self.select_dropdown_by_visible_text(self.SORT_DROPDOWN, visible_text)