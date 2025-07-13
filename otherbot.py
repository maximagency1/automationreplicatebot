import os
import time
import json
from datetime import datetime
import undetected_chromedriver as uc
from dotenv import load_dotenv
from faker import Faker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

def create_new_user(driver, wait, admin_email):
    """
    Handles the creation of a new user using a tabbing strategy.
    """
    print("Starting user creation process...")
    fake = Faker()

    first_name = fake.first_name()
    last_name = fake.last_name()
    domain = admin_email.split('@')[1]
    new_email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
    password = "Octombrie2005#"

    user_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": new_email,
        "password": password,
        "created_at": datetime.now().isoformat()
    }
    
    print(f"Generated new user: {new_email}")

    try:
        # --- Fill out the user creation form using Tab to navigate ---
        email_username = new_email.split('@')[0]

        # Start with the first name field
        first_name_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@data-test-id='fname']")))
        
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
        
        # Uncheck the "force password change" checkbox using the label text.
        force_change_checkbox_xpath = "//span[text()='Force user to change password on first log in']/preceding-sibling::span/input"
        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, force_change_checkbox_xpath)))
        if checkbox.is_selected():
            print("Unchecking 'force password change'...")
            # We may need to click the label itself if the input is not directly clickable
            driver.execute_script("arguments[0].click();", checkbox)

        # Click the final 'Add' button to create the user.
        add_user_button_xpath = "//button[contains(., 'Add') and not(@disabled)]"
        wait.until(EC.element_to_be_clickable((By.XPATH, add_user_button_xpath))).click()
        print("Submitted the new user form.")

        # Give it a moment for the user to be created.
        time.sleep(5)

        # Save user data to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join("output", f"user_{timestamp}.json")
        with open(output_filename, 'w') as f:
            json.dump(user_data, f, indent=4)
        print(f"Successfully created user and saved data to {output_filename}")
        
        return user_data

    except Exception as e:
        print(f"Failed to create new user. The tabbing strategy may have failed. Error: {e}")
        return None


def register_on_replicate(driver, wait, user_data):
    """
    Handles registering on Replicate by creating a new GitHub account.
    """
    print("\n--- Starting Replicate Registration ---")
    
    # 1. Clear cookies to start a fresh session
    print("Clearing all browser cookies...")
    driver.delete_all_cookies()
    time.sleep(2)

    # 2. Navigate to Replicate sign-in page
    print("Navigating to https://replicate.com/signin...")
    driver.get("https://replicate.com/signin")

    # 3. Click "Sign in with GitHub" button
    try:
        github_button_xpath = "//a[contains(., 'Sign in with GitHub')]"
        github_button = wait.until(EC.element_to_be_clickable((By.XPATH, github_button_xpath)))
        print("Clicking 'Sign in with GitHub' button...")
        github_button.click()

        print("\nSuccessfully navigated to GitHub page. Looking for 'Create an account' link...")
        
        # Click "Create an account" on the GitHub page.
        create_account_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Create an account")))
        print("Clicking 'Create an account'...")
        create_account_link.click()

        print("\nSuccessfully navigated to GitHub sign-up page.")
        print("The next step is to fill the GitHub sign-up form.")
        print("Pausing script. Please provide instructions or HTML for the form.")
        
        return True

    except Exception as e:
        print(f"Failed during Replicate/GitHub navigation. Error: {e}")
        return False


def main():
    """
    Main function to run the Selenium bot.
    """
    load_dotenv()

    # Create output directory if it doesn't exist
    if not os.path.exists("output"):
        os.makedirs("output")
        
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # --- New Cookie & LocalStorage Login Logic ---
        zoho_cookie_file = "zoho_cookies.json"
        zoho_localstorage_file = "zoho_localstorage.json"

        if os.path.exists(zoho_cookie_file) and os.path.exists(zoho_localstorage_file):
            print("Session files found. Attempting to log in using session data.")
            driver.get("https://mailadmin.zoho.eu")
            time.sleep(2)
            
            # Inject Local Storage
            with open(zoho_localstorage_file, 'r') as f:
                local_storage_data = json.load(f)
            for key, value in local_storage_data.items():
                driver.execute_script(f"window.localStorage.setItem('{key}', '{json.dumps(value)}');")
            print("Local Storage injected.")

            # Inject Cookies
            with open(zoho_cookie_file, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                try:
                    if 'sameSite' in cookie:
                        del cookie['sameSite']
                    driver.add_cookie(cookie)
                except Exception as e:
                    pass # Ignore problematic cookies
            print("Cookies injected.")

            print("Refreshing the page...")
            driver.refresh()
            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Users']")))
            print("Successfully logged in using session data.")

        else:
            print("Session files not found. Falling back to username/password login.")
            print("NOTE: This may fail due to rate limits. Using cookies is recommended.")
            zoho_email = os.getenv("ZOHO_EMAIL")
            zoho_password = os.getenv("ZOHO_PASSWORD")
            if not all([zoho_email, zoho_password]):
                print("Error: Missing Zoho credentials in .env file.")
                return

            driver.get("https://accounts.zoho.eu/signin?servicename=VirtualOffice&signupurl=https://www.zoho.com/mail/zohomail-pricing.html&serviceurl=https://mail.zoho.eu")
            wait.until(EC.visibility_of_element_located((By.ID, "login_id"))).send_keys(zoho_email)
            wait.until(EC.element_to_be_clickable((By.ID, "nextbtn"))).click()
            wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(zoho_password)
            wait.until(EC.element_to_be_clickable((By.ID, "nextbtn"))).click()
            
            try:
                skip_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="confirm_form1"]/div[3]/button')))
                skip_button.click()
            except Exception:
                pass # Ignore if not found
            
            driver.get("https://mailadmin.zoho.eu")

        # --- The rest of the logic remains the same ---
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Users']"))).click()
        
        add_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[(self::a or self::button) and contains(., 'Add')]")))
        add_button.click()
        
        user_creation_attempted = False
        new_user_data = None
        try:
            # Check for license limit pop-up
            wait.until(EC.visibility_of_element_located((By.XPATH, "//*[text()='License limit reached']")))
            print("License limit reached. Deleting a user...")
            
            close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']")))
            close_button.click()
            time.sleep(2)
            
            # --- Deletion Logic ---
            user_row_xpath = "//*[self::tr or @role='row'][contains(., '@') and not(contains(., 'maxim@joinkoreautomation.com'))][1]"
            user_row = wait.until(EC.presence_of_element_located((By.XPATH, user_row_xpath)))
            delete_button_xpath = ".//button[contains(@aria-label, 'Delete') or .//i[contains(@class, 'trash') or contains(@class, 'delete')]]"
            delete_button = user_row.find_element(By.XPATH, delete_button_xpath)
            delete_button.click()
            time.sleep(2)
            confirm_button_xpath = "//*[@role='dialog']//button[contains(., 'Delete') or contains(., 'Confirm')]"
            confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))
            confirm_button.click()
            time.sleep(5)
            
            # Retry adding user
            add_button_retry = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[(self::a or self::button) and contains(., 'Add')]")))
            add_button_retry.click()
            
            new_user_data = create_new_user(driver, wait, zoho_email)
            user_creation_attempted = True

        except Exception:
            # If the pop-up didn't appear, we are on the "Add User" page.
            print("No license limit pop-up. Proceeding to create user...")
            pass # Continue to the user creation call below

        if not user_creation_attempted:
            new_user_data = create_new_user(driver, wait, zoho_email)

        if new_user_data:
            print("\nZoho user creation successful. Proceeding to Replicate registration.")
            register_on_replicate(driver, wait, new_user_data)
        else:
            print("\nZoho user creation failed. Stopping the script.")

        print("Pausing before closing...")
        time.sleep(10)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing the browser.")
        driver.quit()

if __name__ == "__main__":
    main() 