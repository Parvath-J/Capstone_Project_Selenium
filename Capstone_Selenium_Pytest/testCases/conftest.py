# testCases/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import allure
from allure_commons.types import AttachmentType


# Command-line option to specify browser
def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome",
                     help="Browser to run tests on: chrome, firefox, edge")


# Fixture to initialize and quit the driver
@pytest.fixture(scope="class")
def setup(request):
    browser_name = request.config.getoption("browser").lower()

    if browser_name == "chrome":
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    elif browser_name == "firefox":
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    elif browser_name == "edge":
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
    else:
        raise pytest.UsageError("--browser option is invalid, choose from chrome/firefox/edge")

    driver.implicitly_wait(10)
    driver.maximize_window()
    request.cls.driver = driver
    yield
    driver.quit()


# Hook to add screenshot to Allure report on test failure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()
    if report.when == 'call' and report.failed:
        try:
            driver = item.cls.driver
            allure.attach(driver.get_screenshot_as_png(), name="screenshot_on_failure",
                          attachment_type=AttachmentType.PNG)
        except Exception as e:
            print(f"Failed to take screenshot: {e}")