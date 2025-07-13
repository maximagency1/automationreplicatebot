import os
import json
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from faker import Faker

# --- Configuration ---
CREDENTIALS_FILE = 'credentials.json'
SESSION_FILE = 'session.json'
USERS_FILE = 'users.json'
ZOHO_BASE_URL = 'https://accounts.zoho.eu/'
ADMIN_CONSOLE_URL = 'https://mailadmin.zoho.eu/cpanel/home.do'


def handle_verification_tab(driver):
    """Checks for and handles the 'Verify Your Identity' tab."""
    print("Checking for verification tab...")
    original_window = driver.current_window_handle
    try:
        # Wait for a new tab to open, with a short timeout
        WebDriverWait(driver, 5).until(EC.number_of_windows_to_be(2))
        all_windows = driver.window_handles
        new_window = [window for window in all_windows if window != original_window][0]
        driver.switch_to.window(new_window)

        if "Verify" in driver.title:
            print("Verification tab found. Entering password...")
            password_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.NAME, "password")))
            password_field.send_keys("Octombrie2005#")
            password_field.send_keys(Keys.ENTER)
            print("Password submitted. Waiting for verification to complete...")
            time.sleep(5) # Wait for the page to process
            print("Closing verification tab.")
            driver.close()
            driver.switch_to.window(original_window)
            print("Verification successful. Re-saving session...")
            save_session_data(driver)
            return True
        else:
            # Not the tab we expected, switch back.
            driver.switch_to.window(original_window)

    except TimeoutException:
        # No new tab appeared, which is fine.
        print("No verification tab found.")
        pass
    return False

def save_session_data(driver):
    """Saves cookies and local storage to a file."""
    print("Saving session data...")
    data = {
        'cookies': driver.get_cookies(),
        'localStorage': driver.execute_script("return window.localStorage;")
    }
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Session data saved successfully to {SESSION_FILE}")


def load_session_data(driver):
    """Loads cookies and local storage from a file."""
    print(f"Attempting to load session from {SESSION_FILE}...")
    try:
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)

        # Navigate to the domain to set cookies before loading them
        driver.get(ZOHO_BASE_URL)
        print(f"Navigated to {ZOHO_BASE_URL} to set session data.")
        time.sleep(2)

        for cookie in data.get('cookies', []):
            if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                del cookie['sameSite']
            driver.add_cookie(cookie)
        print("Cookies loaded.")

        local_storage = data.get('localStorage', {})
        driver.execute_script("var data = arguments[0]; for (var key in data) { window.localStorage.setItem(key, data[key]); }", local_storage)
        print("Local storage loaded.")

        driver.refresh()
        print("Page refreshed to apply session.")
        return True
    except FileNotFoundError:
        print("Session file not found. A new one will be created after login.")
        return False
    except Exception as e:
        print(f"An error occurred while loading session data: {e}")
        return False


def perform_login(driver):
    """Performs a one-time login and pauses for manual intervention."""
    print("Performing first-time login...")
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials = json.load(f)
    except FileNotFoundError:
        print(f"FATAL: {CREDENTIALS_FILE} not found. Please create it.")
        return False

    driver.get(ZOHO_BASE_URL + 'signin')

    try:
        email_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'login_id'))
        )
        email_input.send_keys(credentials['email'])
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'nextbtn'))).click()
        print("Email entered.")

        password_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'password'))
        )
        password_input.send_keys(credentials['password'])
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'nextbtn'))).click()
        print("Password entered.")

        print("\n>>> ACTION REQUIRED <<<")
        print("Login submitted. Please complete any manual steps (like 'skip for now').")
        print("The script will wait for 45 seconds before saving your session.")
        time.sleep(45)
        print("Resuming script...")

        save_session_data(driver)
        return True

    except Exception as e:
        print(f"An error occurred during the login process: {e}")
        return False


def create_new_user(driver):
    """Creates a new user with dummy data using the tabbing strategy."""
    print("--- Starting User Creation ---")
    fake = Faker()
    first_name = fake.first_name()
    last_name = fake.last_name()
    # Assume the domain from the credentials, or use a placeholder
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds = json.load(f)
            domain = creds['email'].split('@')[1]
    except Exception:
        domain = "example.com"

    email_username = f"{first_name.lower()}.{last_name.lower()}"
    new_email = f"{email_username}@{domain}"
    password = f"{fake.password(length=12, special_chars=True, upper_case=True, lower_case=True, digits=True)}#"

    print(f"Generated new user: {new_email}")

    try:
        # Start with the first name field using the stable data-test-id selector
        print("Waiting for the user creation form to be ready...")
        first_name_field = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//input[@data-test-id='fname']")))
        
        # Fill form by tabbing through fields
        first_name_field.send_keys(first_name)
        print("Filled First Name.")
        first_name_field.send_keys(Keys.TAB)
        
        driver.switch_to.active_element.send_keys(last_name)
        print("Filled Last Name.")
        driver.switch_to.active_element.send_keys(Keys.TAB)
        
        driver.switch_to.active_element.send_keys(email_username)
        print("Filled Email (Username).")
        driver.switch_to.active_element.send_keys(Keys.TAB)

        driver.switch_to.active_element.send_keys(password)
        print("Filled Password.")
        driver.switch_to.active_element.send_keys(Keys.TAB)

        driver.switch_to.active_element.send_keys(password)
        print("Filled Confirm Password.")
        
        # Uncheck the "force password change" checkbox
        force_change_checkbox_xpath = "//span[text()='Force user to change password on first log in']/preceding-sibling::span/input"
        checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, force_change_checkbox_xpath)))
        if checkbox.is_selected():
            print("Unchecking 'force password change'...")
            driver.execute_script("arguments[0].click();", checkbox)

        # Click the final 'Add' button to create the user.
        add_user_button_xpath = "//button[contains(., 'Add') and not(@disabled)]"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, add_user_button_xpath))).click()
        print("Submitted the new user form.")
        time.sleep(5)
        print(f"Successfully created user: {new_email}")
        return True

    except Exception as e:
        print(f"Failed to create new user. Error: {e}")
        return False

def add_new_user(driver):
    """Navigates directly to the user list and then clicks 'Add User'."""
    user_list_url = 'https://mailadmin.zoho.eu/cpanel/home.do#users/list'
    print(f"Navigating directly to user list: {user_list_url}")
    driver.get(user_list_url)
    time.sleep(10) # Wait for the page and any scripts to load

    try:
        # Using the successful strategy from the other bot.
        # This selector finds any 'a' or 'button' element containing the text 'Add'.
        print("Looking for 'Add' button using the proven XPath selector...")
        add_button_xpath = "//*[(self::a or self::button) and contains(., 'Add')]"
        add_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, add_button_xpath))
        )
        print("Found 'Add' button, clicking it...")
        add_button.click()
        handle_verification_tab(driver) # Check for verification after clicking 'Add'
        time.sleep(2)

        try:
            # Check for the license limit pop-up, with a short timeout.
            print("Checking for 'License limit reached' pop-up...")
            limit_popup_text = (By.XPATH, "//*[text()='License limit reached']")
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located(limit_popup_text))

            # If found, close it.
            print("Found 'License limit reached' pop-up. Closing it...")
            close_button_xpath = "//button[@aria-label='Close']"
            close_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, close_button_xpath)))
            close_button.click()
            print("Pop-up closed. Proceeding to delete a user to make space...")
            time.sleep(2)

            # --- Deletion Logic from otherbot.py ---
            print("Finding a user to delete (excluding maxim@joinkoreautomation.com)...")
            user_row_xpath = "//*[self::tr or @role='row'][contains(., '@') and not(contains(., 'maxim@joinkoreautomation.com'))][1]"
            user_row = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, user_row_xpath)))

            print("Found user row. Finding delete button...")
            delete_button_xpath = ".//button[contains(@aria-label, 'Delete') or .//i[contains(@class, 'trash') or contains(@class, 'delete')]]"
            delete_button = user_row.find_element(By.XPATH, delete_button_xpath)
            delete_button.click()
            time.sleep(2)

            print("Confirming deletion...")
            confirm_button_xpath = "//*[@role='dialog']//button[contains(., 'Delete') or contains(., 'Confirm')]"
            confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))
            confirm_button.click()
            print("User deleted successfully.")
            time.sleep(2)
            handle_verification_tab(driver) # Check for verification after deletion
            time.sleep(3)

            # --- Retry adding user ---
            print("Retrying to click the 'Add' button...")
            add_button_retry_xpath = "//*[(self::a or self::button) and contains(., 'Add')]"
            add_button_retry = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, add_button_retry_xpath)))
            driver.execute_script("arguments[0].click();", add_button_retry) # Use JS click to avoid interception
            print("'Add' button clicked again.")

            # Now, we should be on the form page. Create the user.
            create_new_user(driver)

        except TimeoutException:
            # If the pop-up didn't appear, we are on the user creation form.
            print("No license limit pop-up found. Proceeding to create user...")
            create_new_user(driver)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\n--- ACTION REQUIRED ---")
        print("The script failed to find the 'Add User' button or a form field.")
        print("Please inspect the page and provide the correct CSS selector or XPath for the element that could not be found.")
    finally:
        driver.switch_to.default_content()


def main():
    """Main function to run the bot."""
    driver = None
    try:
        print("Initializing Chrome driver...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = uc.Chrome(options=options, use_subprocess=True)
        print("Setting window size and position...")
        driver.set_window_size(800, 600)
        driver.set_window_position(0, 0)

        if not os.path.exists(SESSION_FILE) or not load_session_data(driver):
            print("No valid session found. Starting login process.")
            if not perform_login(driver):
                return # Exit if login fails

        print("Session is active. Navigating to the admin console.")
        driver.get(ADMIN_CONSOLE_URL)
        time.sleep(5) # Wait for page to load

        add_new_user(driver)

        print("\nScript has finished its task.")

    except Exception as e:
        print(f"An unexpected error occurred in main: {e}")
    finally:
        if driver:
            print("Closing browser in 10 seconds...")
            time.sleep(10)
            driver.quit()


if __name__ == '__main__':
    main()
