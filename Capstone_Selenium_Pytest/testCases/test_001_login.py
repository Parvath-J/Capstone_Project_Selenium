# testCases/test_001_login.py
import pytest
from pageObjects.LoginPage import LoginPage
from pageObjects.InventoryPage import InventoryPage
from utilities.readConfig import ReadConfig
from utilities.customLogger import LogGen


@pytest.mark.usefixtures("setup")
class Test_001_Login:
    baseURL = ReadConfig.getApplicationURL()
    logger = LogGen.loggen()

    @pytest.mark.regression
    def test_page_title(self):
        self.logger.info("**** Starting test_page_title ****")
        self.driver.get(self.baseURL)
        actual_title = self.driver.title
        if actual_title == "Swag Labs":
            assert True
            self.logger.info("**** Page title test passed ****")
        else:
            self.logger.error("**** Page title test failed ****")
            assert False

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_login_positive(self):
        self.logger.info("**** Starting test_login_positive ****")
        self.driver.get(self.baseURL)
        self.login_page = LoginPage(self.driver)
        self.login_page.set_username(ReadConfig.getUsername())
        self.login_page.set_password(ReadConfig.getPassword())
        self.login_page.click_login()

        self.inventory_page = InventoryPage(self.driver)
        page_title = self.inventory_page.get_page_title()

        if page_title == "Products":
            assert True
            self.logger.info("**** Login positive test passed ****")
        else:
            self.logger.error("**** Login positive test failed ****")
            assert False