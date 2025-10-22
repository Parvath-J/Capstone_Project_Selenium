# testCases/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager # No longer needed for manual Chrome
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager  # Keep for Firefox
from selenium.webdriver.edge.service import Service as EdgeService
# No webdriver_manager needed for manual Edge
import allure
from allure_commons.types import AttachmentType
import os
from datetime import datetime
import base64


# Command-line option to specify browser
def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome",
                     help="Browser to run tests on: chrome, firefox, edge")


@pytest.fixture(scope="class")
def setup(request):
    browser_name = request.config.getoption("browser").lower()

    if browser_name == "chrome":
        chrome_options = webdriver.ChromeOptions()
        # Keep options if needed, e.g., for headless runs in CI
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # --- USE MANUAL PATH FOR CHROME ---
        chrome_driver_path = "./drivers/chromedriver.exe"  # Path to your downloaded chromedriver
        service = ChromeService(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        # --- END OF CHROME MODIFICATION ---

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

    elif browser_name == "edge":
        # --- EDGE USES MANUAL PATH (As before) ---
        edge_driver_path = "./drivers/msedgedriver.exe"  # Path to your downloaded msedgedriver
        service = EdgeService(executable_path=edge_driver_path)
        driver = webdriver.Edge(service=service)
        # Add Edge options here if needed, e.g., for headless (though complex on Linux)
        # edge_options = webdriver.EdgeOptions()
        # edge_options.add_argument("--headless")
        # driver = webdriver.Edge(service=service, options=edge_options)

    else:
        raise pytest.UsageError("--browser option is invalid, choose from chrome/firefox/edge")

    driver.implicitly_wait(10)
    # driver.maximize_window() # Keep commented out if running headless/in CI
    request.cls.driver = driver
    yield
    driver.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    pytest_html = item.config.pluginmanager.getplugin("html")
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, "extra", [])

    if report.when == "call" and report.failed:
        try:
            driver = item.cls.driver

            # --- Save Screenshot File (Optional) ---
            screenshot_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{item.name}_{timestamp}.png"
            file_path = os.path.join(screenshot_dir, filename)
            driver.save_screenshot(file_path)

            # --- Embed Screenshot in HTML Report ---
            screenshot_png = driver.get_screenshot_as_png()
            encoded_image = base64.b64encode(screenshot_png).decode("utf-8")
            img_html = f'<img src="data:image/png;base64,{encoded_image}" style="width:60%;"/>'
            extra.append(pytest_html.extras.html(img_html))

            # --- Attach screenshot to Allure report ---
            allure.attach(screenshot_png, name="screenshot_on_failure",
                          attachment_type=AttachmentType.PNG)

        except Exception as e:
            print(f"Failed to take/process screenshot: {e}")

    report.extra = extra

