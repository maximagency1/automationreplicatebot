# PRD: Zoho User Creation Automation Bot

## 1. Objective

The primary objective of this project is to develop an automation bot that programmatically adds new users to the Zoho Admin Console. The bot will use a pre-existing authenticated browser session to bypass the login process, create users with dummy information, and store their credentials for future reference.

## 2. Features

- **Automated User Creation**: The bot will navigate to the user creation section within the Zoho Admin Console.
- **Dummy Data Population**: It will fill in the required user information fields (e.g., first name, last name, username/email) with placeholder data.
- **One-Time Login & Session Caching**: On its first run, the bot will log in to Zoho using credentials from `credentials.json`. It will then save the session data (cookies, local storage) to a local file.
- **Automated Session Reuse**: On subsequent runs, the bot will load the cached session data to bypass login and gain immediate access.
- **Credential Storage**: Upon successful user creation, the bot will save the new user's email and password to a local JSON file named `users.json`.

## 3. Technical Requirements

- **Language**: Python
- **Core Library**: `selenium` with `undetected-chromedriver` to avoid bot detection.
- **Browser**: Google Chrome or a compatible Chromium-based browser.
- **Input**:
    - `credentials.json`: A file containing the admin email and password for the initial login.
    - `session.json` (Generated): A file to store session data after the first login.
- **Output**: `users.json`: A file containing the details of newly created users.

## 4. Data Storage (`users.json`)

The bot will generate and maintain a `users.json` file. Each entry in the file will be a JSON object with the following structure:

```json
[
  {
    "email": "dummyuser1@example.com",
    "password": "aGeneratedPassword123",
    "sessionId": "someSessionIdentifier..."
  }
]
```

## 5. Authentication Flow

1.  The bot is launched.
2.  It checks for the existence of a `session.json` file.
3.  **If `session.json` does not exist (First Run)**:
    a. The bot reads the email and password from `credentials.json`.
    b. It navigates to the Zoho login page and enters the credentials to log in.
    c. Upon successful login, it navigates to the Admin Console, then extracts the session cookies and local storage data.
    d. The bot saves this session data into a new `session.json` file.
4.  **If `session.json` exists (Subsequent Runs)**:
    a. The bot loads the Zoho Admin Console URL.
    b. It injects the cookies and local storage data from `session.json` to restore the session.

## 6. On-Demand Identity Verification

- **Trigger**: The bot must handle cases where Zoho requires identity verification, which can happen when adding or deleting a user.
- **Behavior**: Zoho will open a new browser tab with a page titled "Verify Your Identity".
- **Action**: The bot must detect the new tab, switch to it, enter the admin password (`Octombrie2005#`) into the password field, and submit the form.
- **Session Update**: After successful verification, the bot must immediately re-save the browser session (cookies and local storage) to `session.json`. This updates the session with the new verification status, reducing the frequency of future checks.
5.  The bot proceeds with the user creation workflow.

## 6. Out of Scope

- **User Deletion/Modification**: This version will only focus on adding new users.
- **User Deletion/Modification**: This version will only focus on adding new users.
- **Error Handling for Invalid Sessions**: The bot will assume the provided session data is valid and active. Advanced error handling for expired or invalid sessions is not included in this scope.
- **Graphical User Interface (GUI)**: The bot will operate as a command-line script.