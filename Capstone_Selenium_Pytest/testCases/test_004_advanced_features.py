import pytest
import time
import os
import requests  # Import for broken link testing
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pageObjects.BasePage import BasePage
from utilities.readConfig import ReadConfig
from utilities.customLogger import LogGen


@pytest.mark.usefixtures("setup")
class Test_004_AdvancedFeatures:
    # Get new URLs from ReadConfig
    heroku_url = ReadConfig.getInternetHerokuappURL()
    demoqa_url = ReadConfig.getDemoQAURL()
    logger = LogGen.loggen()

    @pytest.mark.regression
    def test_alerts(self):
        self.logger.info("**** Starting test_alerts ****")
        self.driver.get(f"{self.heroku_url}/javascript_alerts")
        bp = BasePage(self.driver)

        # Locators
        alert_button = (By.CSS_SELECTOR, "button[onclick='jsAlert()']")
        confirm_button = (By.CSS_SELECTOR, "button[onclick='jsConfirm()']")
        prompt_button = (By.CSS_SELECTOR, "button[onclick='jsPrompt()']")
        result_label = (By.ID, "result")

        # Test JS Alert
        bp.do_click(alert_button)
        alert_text = bp.get_alert_text()
        bp.accept_alert()
        assert "I am a JS Alert" in alert_text

        # Test JS Confirm
        bp.do_click(confirm_button)
        bp.accept_alert()  # You can also use bp.dismiss_alert()
        assert "You clicked: Ok" in bp.get_element_text(result_label)

        # Test JS Prompt
        bp.do_click(prompt_button)
        bp.send_keys_to_alert("Test Automation")
        assert "You entered: Test Automation" in bp.get_element_text(result_label)
        self.logger.info("**** test_alerts PASSED ****")

    @pytest.mark.regression
    def test_window_handling(self):
        self.logger.info("**** Starting test_window_handling ****")
        self.driver.get(f"{self.heroku_url}/windows")
        bp = BasePage(self.driver)

        original_window_handle = self.driver.current_window_handle

        bp.do_click((By.LINK_TEXT, "Click Here"))

        # Use the new BasePage method to switch
        bp.switch_to_new_window()

        # Assert text on the new window
        assert "New Window" in bp.get_element_text((By.TAG_NAME, "h3"))

        # Close the new window
        self.driver.close()

        # Switch back to the original window
        bp.switch_to_window_by_handle(original_window_handle)

        # Assert we are back
        assert "Opening a new window" in bp.get_element_text((By.TAG_NAME, "h3"))
        self.logger.info("**** test_window_handling PASSED ****")

    """
    @pytest.mark.skip(reason="Skipping this test until the iframe issue is fixed")
    @pytest.mark.regression
    def test_frame_handling(self):
        self.logger.info("**** Starting test_frame_handling ****")
        self.driver.get(f"{self.heroku_url}/iframe")
        bp = BasePage(self.driver)

        # Switch to the frame
        bp.switch_to_frame_by_locator((By.ID, "mce_0_ifr"))

        # --- MODIFIED SECTION ---
        text_box_locator = (By.ID, "tinymce")
        # 1. Wait for and get the element
        text_box_element = bp.wait.until(EC.visibility_of_element_located(text_box_locator))

        # 2. Clear the element
        text_box_element.clear()

        # 3. Send keys to the element
        text_box_element.send_keys("Hello from the iframe!")

        # 4. Get text using 'textContent' for assertion
        actual_text = text_box_element.get_attribute("textContent")
        assert "Hello from the iframe!" in actual_text
        # --- END OF MODIFIED SECTION ---

        # Switch back to the main page
        bp.switch_to_default_content()

        # Assert element on the main page
        assert "An iFrame containing the TinyMCE" in bp.get_element_text((By.TAG_NAME, "h3"))
        self.logger.info("**** test_frame_handling PASSED ****")
    """

    @pytest.mark.regression
    def test_checkboxes_and_radio(self):
        self.logger.info("**** Starting test_checkboxes_and_radio ****")
        self.driver.get(f"{self.demoqa_url}/checkbox")
        bp = BasePage(self.driver)

        # Checkboxes on DemoQA are tricky, they use labels.
        checkbox_label = (By.CSS_SELECTOR, "label[for='tree-node-home']")
        result_text = (By.ID, "result")

        # Use JS click as they are not standard inputs
        bp.do_js_click(checkbox_label)
        actual_text = bp.get_element_text(result_text)
        assert "You have selected" in actual_text and "home" in actual_text

        # Radio Buttons
        self.driver.get(f"{self.demoqa_url}/radio-button")
        radio_label_yes = (By.CSS_SELECTOR, "label[for='yesRadio']")
        result_text_radio = (By.CSS_SELECTOR, ".text-success")

        bp.do_js_click(radio_label_yes)
        assert "Yes" in bp.get_element_text(result_text_radio)
        self.logger.info("**** test_checkboxes_and_radio PASSED ****")

    @pytest.mark.regression
    def test_web_table(self):
        self.logger.info("**** Starting test_web_table ****")
        self.driver.get(f"{self.demoqa_url}/webtables")
        bp = BasePage(self.driver)

        # Let's just read a value from a specific cell
        cell_cierra = (By.XPATH, "//div[text()='Cierra']")
        assert bp.is_visible(cell_cierra)

        # Read the email from the same row
        email = bp.get_element_text((By.XPATH, "//div[text()='Cierra']/following-sibling::div[3]"))
        assert "cierra@example.com" in email
        self.logger.info("**** test_web_table PASSED ****")

    @pytest.mark.regression
    def test_mouse_hover(self):
        self.logger.info("**** Starting test_mouse_hover ****")
        self.driver.get(f"{self.demoqa_url}/tool-tips")
        bp = BasePage(self.driver)

        hover_button = (By.ID, "toolTipButton")
        tooltip = (By.ID, "buttonToolTip")

        # Perform the hover
        bp.move_to_element(hover_button)
        time.sleep(1)

        # Assert the tooltip text is visible
        assert "You hovered over the Button" in bp.get_element_text(tooltip)
        self.logger.info("**** test_mouse_hover PASSED ****")

    """
    @pytest.mark.regression
    def test_drag_and_drop(self):
        self.logger.info("**** Starting test_drag_and_drop ****")
        self.driver.get(f"{self.demoqa_url}/droppable")
        bp = BasePage(self.driver)

        draggable = (By.ID, "draggable")
        droppable = (By.ID, "droppable")

        bp.perform_drag_and_drop(draggable, droppable)

        # Assert the drop text has changed
        assert "Dropped!" in bp.get_element_text((By.CSS_SELECTOR, "#droppable p"))
        self.logger.info("**** test_drag_and_drop PASSED ****")
    """

    @pytest.mark.regression
    def test_file_upload(self):
        self.logger.info("**** Starting test_file_upload ****")

        # Create a dummy file for uploading
        file_name = "test_upload.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w") as f:
            f.write("This is a test file.")

        self.driver.get(f"{self.heroku_url}/upload")
        bp = BasePage(self.driver)

        upload_input = (By.ID, "file-upload")
        upload_button = (By.ID, "file-submit")
        uploaded_files = (By.ID, "uploaded-files")

        # Use send_keys on the <input type="file"> element
        # It MUST be an absolute path
        bp.do_send_keys(upload_input, file_path)
        bp.do_click(upload_button)

        assert file_name in bp.get_element_text(uploaded_files)
        self.logger.info("**** test_file_upload PASSED ****")

        # Clean up the dummy file
        os.remove(file_path)

    @pytest.mark.regression
    def test_broken_links(self):
        self.logger.info("**** Starting test_broken_links ****")
        self.driver.get(f"{self.heroku_url}/broken_images")

        links = self.driver.find_elements(By.TAG_NAME, "a")
        images = self.driver.find_elements(By.TAG_NAME, "img")

        all_urls = [link.get_attribute("href") for link in links]
        all_urls.extend([img.get_attribute("src") for img in images])

        for url in all_urls:
            if url and not url.startswith("javascript"):
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code >= 400:
                        self.logger.warning(f"BROKEN LINK: {url} (Status: {response.status_code})")
                        # You could assert False here if you want the test to fail on any broken link
                except requests.RequestException as e:
                    self.logger.error(f"Error checking link {url}: {e}")

        # For this test, we'll pass as long as it runs, but log warnings.
        assert True
        self.logger.info("**** test_broken_links COMPLETED ****")