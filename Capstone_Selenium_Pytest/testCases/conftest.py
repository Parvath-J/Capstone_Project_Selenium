# testCases/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
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
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        # --- THIS LINE IS MODIFIED ---
        # Pass the options when creating the driver instance
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    elif browser_name == "firefox":
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument("--headless")
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)
    elif browser_name == "edge":
        edge_driver_path = "./drivers/msedgedriver.exe"
        service = EdgeService(executable_path=edge_driver_path)
        driver = webdriver.Edge(service=service) # Note: Headless Edge on Linux in Actions is complex
    else:
        raise pytest.UsageError("--browser option is invalid, choose from chrome/firefox/edge")

    driver.implicitly_wait(10)
    # driver.maximize_window() # Keep this commented out for headless
    request.cls.driver = driver
    yield
    driver.quit()

# --- (Rest of the file remains the same) ---

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
            # print(f"Screenshot saved to: {file_path}") # Optional

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