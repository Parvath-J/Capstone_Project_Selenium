#___________________________________________________________________________________________
# testCases/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
import allure
from allure_commons.types import AttachmentType
import os
from datetime import datetime
import base64


# -------------------------------------------------------
# Command-line option for browser selection
# -------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="firefox",  # Default browser is FIREFOX
        help="Browser(s) to run tests on: chrome, firefox, edge, or all"
    )


# -------------------------------------------------------
# Fixture to initialize the WebDriver
# -------------------------------------------------------
@pytest.fixture(scope="class")
def setup(request):
    browser_name = request.config.getoption("browser").lower()

    # --- when browser=all, run only firefox & edge ---
    if browser_name == "all":
        browser_list = ["firefox", "edge"]
    else:
        browser_list = [browser_name]

    # store first browser only for now (pytest-xdist will split)
    current_browser = browser_list[0]

    if current_browser == "chrome":
        chrome_driver_path = "./drivers/chromedriver.exe"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        service = ChromeService(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

    elif browser_name == "firefox":
        # --- USE MANUAL PATH FOR FIREFOX ---
        firefox_driver_path = "./drivers/geckodriver.exe"  # Path to your downloaded geckodriver
        service = FirefoxService(executable_path=firefox_driver_path)

        firefox_options = webdriver.FirefoxOptions()
        # --- ADD THIS LINE ---
        firefox_options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"  # <-- **PUT YOUR ACTUAL PATH HERE**
        # --- END OF ADDED LINE ---

        # Add headless option if you run Firefox headlessly
        # firefox_options.add_argument("--headless")

        driver = webdriver.Firefox(service=service, options=firefox_options)
        # --- END OF FIREFOX MODIFICATION ---

    elif current_browser == "edge":
        edge_driver_path = "./drivers/msedgedriver.exe"
        service = EdgeService(executable_path=edge_driver_path)
        driver = webdriver.Edge(service=service)

    else:
        raise pytest.UsageError("--browser option invalid, choose from chrome/firefox/edge/all")

    driver.implicitly_wait(10)
    driver.maximize_window()
    request.cls.driver = driver
    yield
    driver.quit()


# -------------------------------------------------------
# Generate param sets for pytest-xdist parallel browser runs
# -------------------------------------------------------
def pytest_generate_tests(metafunc):
    if "setup" in metafunc.fixturenames:
        browser_option = metafunc.config.getoption("browser").lower()

        # ✅ only parametrize when user gives --browser=all
        if browser_option == "all":
            metafunc.parametrize("browser_param", ["firefox", "edge"], scope="session")
        else:
            metafunc.parametrize("browser_param", [browser_option], scope="session")


@pytest.fixture(scope="class")
def setup(request, browser_param):
    """Modified setup fixture to use the parameter from pytest_generate_tests"""
    browser_name = browser_param.lower()

    if browser_name == "chrome":
        chrome_driver_path = "./drivers/chromedriver.exe"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        service = ChromeService(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

    elif browser_name == "firefox":
        firefox_options = webdriver.FirefoxOptions()
        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=firefox_options
        )

    elif browser_name == "edge":
        edge_driver_path = "./drivers/msedgedriver.exe"
        service = EdgeService(executable_path=edge_driver_path)
        driver = webdriver.Edge(service=service)

    else:
        raise pytest.UsageError("--browser option invalid, choose from chrome/firefox/edge/all")

    driver.implicitly_wait(10)
    driver.maximize_window()
    request.cls.driver = driver
    yield
    driver.quit()


# -------------------------------------------------------
# Screenshot capture for failed tests (HTML + Allure)
# -------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, "extra", [])

    if report.when == "call" and report.failed:
        try:
            driver = item.cls.driver
            screenshot_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{item.name}_{timestamp}.png"
            file_path = os.path.join(screenshot_dir, filename)
            driver.save_screenshot(file_path)

            screenshot_png = driver.get_screenshot_as_png()
            encoded_image = base64.b64encode(screenshot_png).decode("utf-8")
            img_html = f'<img src="data:image/png;base64,{encoded_image}" style="width:60%;"/>'
            extra.append(pytest_html.extras.html(img_html))

            allure.attach(screenshot_png, name="screenshot_on_failure",
                          attachment_type=AttachmentType.PNG)
        except Exception as e:
            print(f"Failed to take/process screenshot: {e}")

    report.extra = extra
