import json
import time
import undetected_chromedriver as uc

# --- Configuration ---
SESSION_FILE = 'session.json'
DEBUGGER_PORT = 9222 # We will use this port

def save_session_data(driver):
    """Saves cookies and local storage from the connected browser."""
    print("Saving session data...")
    # Navigate to a Zoho domain to ensure we can access local storage
    driver.get("https://accounts.zoho.eu/")
    time.sleep(2) # Wait for page to be responsive
    
    data = {
        'cookies': driver.get_cookies(),
        'localStorage': driver.execute_script("return window.localStorage;")
    }
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Session data saved successfully to {SESSION_FILE}")

def main():
    """Connects to an existing browser and saves its session."""
    driver = None
    try:
        print(f"Attempting to connect to browser on port {DEBUGGER_PORT}...")
        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options, debugger_address=f"127.0.0.1:{DEBUGGER_PORT}")
        
        print("Successfully connected to the browser.")
        save_session_data(driver)

    except Exception as e:
        print(f"An error occurred: {e}")
        print("\\n--- Troubleshooting ---")
        print("1. Make sure the target browser window (the one logged into Zoho) is still open.")
        print(f"2. Make sure Chrome was launched with remote debugging enabled on port {DEBUGGER_PORT}.")
        print("You may need to close Chrome completely and restart it from your terminal with the command:")
        print("'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --remote-debugging-port=9222")
        print("Then, manually log into Zoho again before running this script.")

    finally:
        if driver:
            # We don't quit the driver, as we don't want to close the user's browser
            print("\\nScript finished. The browser session should be saved.")

if __name__ == '__main__':
    main()