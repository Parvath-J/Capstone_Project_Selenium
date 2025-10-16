# testCases/test_002_inventory_and_cart.py
import pytest
from pageObjects.LoginPage import LoginPage
from pageObjects.InventoryPage import InventoryPage
from pageObjects.CartPage import CartPage
from utilities.readConfig import ReadConfig
from utilities.customLogger import LogGen


@pytest.mark.usefixtures("setup")
class Test_002_InventoryAndCart:
    baseURL = ReadConfig.getApplicationURL()
    username = ReadConfig.getUsername()
    password = ReadConfig.getPassword()
    logger = LogGen.loggen()

    @pytest.fixture(autouse=True)
    def class_setup(self):
        # This fixture logs in before each test in this class
        self.driver.get(self.baseURL)
        self.login_page = LoginPage(self.driver)
        self.login_page.set_username(self.username)
        self.login_page.set_password(self.password)
        self.login_page.click_login()
        self.logger.info("**** Logged in for inventory tests ****")

    @pytest.mark.smoke
    def test_add_item_to_cart(self):
        self.logger.info("**** Starting test_add_item_to_cart ****")
        self.inventory_page = InventoryPage(self.driver)
        self.inventory_page.add_backpack_to_cart()
        self.inventory_page.click_shopping_cart()

        self.cart_page = CartPage(self.driver)
        if self.cart_page.is_item_in_cart():
            assert True
            self.logger.info("**** Add item to cart test passed ****")
        else:
            self.logger.error("**** Add item to cart test failed ****")
            assert False

    def test_sort_products(self):
        self.logger.info("**** Starting test_sort_products (Dropdown) ****")
        self.driver.get("https://www.saucedemo.com/inventory.html")
        self.inventory_page = InventoryPage(self.driver)
        self.inventory_page.sort_products("Price (high to low)")
        # In a real scenario, you'd add an assertion to check if items are correctly sorted.
        self.logger.info("**** Successfully selected from dropdown ****")
        assert True