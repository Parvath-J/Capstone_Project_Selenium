# testCases/test_003_checkout_flow.py
import pytest
import time  # <--- IMPORT TIME
from pageObjects.LoginPage import LoginPage
from pageObjects.InventoryPage import InventoryPage
from pageObjects.CartPage import CartPage
from pageObjects.CheckoutStepOnePage import CheckoutStepOnePage
from pageObjects.CheckoutStepTwoPage import CheckoutStepTwoPage
from utilities.readConfig import ReadConfig
from utilities.customLogger import LogGen


@pytest.mark.usefixtures("setup")
class Test_003_Checkout:
    baseURL = ReadConfig.getApplicationURL()
    username = ReadConfig.getUsername()
    password = ReadConfig.getPassword()
    logger = LogGen.loggen()

    @pytest.mark.regression
    def test_end_to_end_checkout(self):
        self.logger.info("**** Starting Test_003_Checkout End-to-End Test ****")

        # 1. Login
        self.driver.get(self.baseURL)
        self.login_page = LoginPage(self.driver)
        self.login_page.set_username(self.username)
        self.login_page.set_password(self.password)
        self.login_page.click_login()

        # 2. Add item to cart
        self.inventory_page = InventoryPage(self.driver)
        self.inventory_page.add_backpack_to_cart()
        self.inventory_page.click_shopping_cart()

        # 3. Go to checkout
        self.cart_page = CartPage(self.driver)
        self.cart_page.click_checkout()

        # 4. Enter checkout info
        self.checkout_one = CheckoutStepOnePage(self.driver)
        self.checkout_one.enter_checkout_info("John", "Doe", "12345")
        self.checkout_one.click_continue()

        # --- DEBUGGING STEP ---
        # We will now pause for 10 seconds to see what page we are on
        print(f"Current URL before failing: {self.driver.current_url}")
        time.sleep(10)

        # 5. Finish checkout and assert
        self.checkout_two = CheckoutStepTwoPage(self.driver)
        total_price = self.checkout_two.get_total_price()
        assert "Total: $32.39" in total_price, "Total price did not match expected"
        self.checkout_two.click_finish()

        # 6. Verify completion
        assert "checkout-complete" in self.driver.current_url
        self.logger.info("**** End-to-End Checkout Test Passed ****")