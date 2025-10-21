import pytest
from pageObjects.LoginPage import LoginPage
from pageObjects.InventoryPage import InventoryPage
from utilities.readConfig import ReadConfig
from utilities.customLogger import LogGen
from utilities import excelUtils
import allure


# --- DATA PROVIDER FUNCTION (MODIFIED) ---
def get_login_data_from_excel():
    file_path = "./testData/login_data.xlsx"
    sheet_name = "LoginData"

    row_count = excelUtils.get_row_count(file_path, sheet_name)
    login_data = []

    for r in range(2, row_count + 1):
        username = excelUtils.read_data(file_path, sheet_name, r, 1)
        password = excelUtils.read_data(file_path, sheet_name, r, 2)
        expected_result = excelUtils.read_data(file_path, sheet_name, r, 3)

        # --- NEW LOGIC HERE ---
        if username == 'locked_out_user':
            # We expect the login to fail. We mark this data row as XFAIL.
            # Pytest will run it, see the 'Fail' logic passes, and mark it as XPASS (unexpectedly passing).
            data_param = pytest.param(username, password, expected_result,
                                      marks=pytest.mark.xfail(reason="User is locked out, expecting fail"))

        elif username == 'problem_user':
            # We want to skip this test row entirely for now.
            data_param = pytest.param(username, password, expected_result,
                                      marks=pytest.mark.skip(reason="Skipping problem_user due to known issue"))

        else:
            # Standard test case, no special marker
            data_param = (username, password, expected_result)

        login_data.append(data_param)
        # --- END OF NEW LOGIC ---

    return login_data


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

    @pytest.mark.skip(reason="Covered by data-driven test")
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_login_positive(self):
        self.logger.info("**** SKIPPED: test_login_positive ****")
        self.driver.get(self.baseURL)
        self.login_page = LoginPage(self.driver)
        self.login_page.set_username(ReadConfig.getUsername())
        self.login_page.set_password(ReadConfig.getPassword())
        self.login_page.click_login()

        self.inventory_page = InventoryPage(self.driver)
        page_title = self.inventory_page.get_page_title()

        if page_title == "Products":
            assert True
        else:
            assert False

    # --- DATA-DRIVEN TEST (Unchanged) ---
    # This test method doesn't need to change.
    # The @parametrize decorator will now get the skip/xfail markers from the data provider.
    @pytest.mark.regression
    @pytest.mark.parametrize("username, password, expected_result", get_login_data_from_excel())
    def test_login_data_driven(self, username, password, expected_result):

        allure.dynamic.title(f"DDT Login Test - User: {username}, Expected: {expected_result}")
        self.logger.info(f"**** Starting test_login_data_driven for {username} ****")

        self.driver.get(self.baseURL)
        self.login_page = LoginPage(self.driver)
        self.login_page.do_robust_send_keys(self.login_page.USERNAME_INPUT, username)
        self.login_page.do_robust_send_keys(self.login_page.PASSWORD_INPUT, password)
        self.login_page.click_login()

        if expected_result == "Pass":
            self.logger.info("Expecting PASS")
            self.inventory_page = InventoryPage(self.driver)
            if self.inventory_page.is_visible(self.inventory_page.PAGE_TITLE):
                assert True
                self.logger.info(f"**** Test PASSED for {username} (Expected: Pass) ****")
            else:
                self.logger.error(f"**** Test FAILED for {username} (Expected: Pass, but not on inventory page) ****")
                assert False

        elif expected_result == "Fail":
            self.logger.info("Expecting FAIL")
            if self.login_page.is_visible(self.login_page.ERROR_MESSAGE_LABEL):
                assert True
                self.logger.info(f"**** Test PASSED for {username} (Expected: Fail, error message shown) ****")
            else:
                self.logger.error(f"**** Test FAILED for {username} (Expected: Fail, but no error found) ****")
                assert False