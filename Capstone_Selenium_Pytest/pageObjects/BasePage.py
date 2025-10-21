# pageObjects/BasePage.py

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert


class BasePage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)  # Use this for all waits

    def do_click(self, by_locator):
        self.wait.until(EC.element_to_be_clickable(by_locator)).click()

    def do_js_click(self, by_locator):
        element = self.wait.until(EC.presence_of_element_located(by_locator))
        self.driver.execute_script("arguments[0].click();", element)

    def do_send_keys(self, by_locator, text):
        self.wait.until(EC.visibility_of_element_located(by_locator)).send_keys(text)

    def do_robust_send_keys(self, by_locator, text):
        element = self.wait.until(EC.element_to_be_clickable(by_locator))
        element.click()
        element.clear()
        element.send_keys(text)

    def get_element_text(self, by_locator):
        element = self.wait.until(EC.visibility_of_element_located(by_locator))
        return element.text

    def is_visible(self, by_locator):
        try:
            element = self.wait.until(EC.visibility_of_element_located(by_locator))
            return element.is_displayed()
        except:
            return False

    def get_title(self, title):
        self.wait.until(EC.title_is(title))
        return self.driver.title

    def select_dropdown_by_visible_text(self, by_locator, text):
        dropdown = Select(self.wait.until(EC.visibility_of_element_located(by_locator)))
        dropdown.select_by_visible_text(text)

    # --- NEW ADVANCED METHODS ---

    def move_to_element(self, by_locator):
        """Performs a mouse hover action on an element."""
        element = self.wait.until(EC.presence_of_element_located(by_locator))
        ActionChains(self.driver).move_to_element(element).perform()

    def perform_drag_and_drop(self, from_locator, to_locator):
        """DrExamples a more robust drag and drop by simulating the full action."""
        element_from = self.wait.until(EC.element_to_be_clickable(from_locator))
        element_to = self.wait.until(EC.element_to_be_clickable(to_locator))

        # Be more explicit: click_and_hold, move, and release AT the target
        actions = ActionChains(self.driver)
        actions.click_and_hold(element_from).move_to_element(element_to).release(element_to).perform()

    def switch_to_frame_by_locator(self, by_locator):
        """Switches the driver context to an iframe."""
        frame = self.wait.until(EC.frame_to_be_available_and_switch_to_it(by_locator))

    def switch_to_default_content(self):
        """Switches the driver context back out of an iframe."""
        self.driver.switch_to.default_content()

    def accept_alert(self):
        """Accepts a JS alert (clicks OK)."""
        self.wait.until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        alert.accept()

    def get_alert_text(self):
        """Gets the text from a JS alert."""
        self.wait.until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        return alert.text

    def send_keys_to_alert(self, text):
        """Sends text to a JS prompt alert."""
        self.wait.until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        alert.send_keys(text)
        alert.accept()

    def switch_to_new_window(self):
        """Switches to the newest window or tab."""
        # Get all window handles
        all_windows = self.driver.window_handles
        # Switch to the last window in the list
        self.driver.switch_to.window(all_windows[-1])

    def switch_to_window_by_handle(self, window_handle):
        """Switches back to a specific window handle."""
        self.driver.switch_to.window(window_handle)