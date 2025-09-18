# Atlassian User & Group Sync

This project contains a Python script that automates the process of fetching user and group data from an Atlassian organization's admin console. It uses Playwright to handle authentication and then interacts directly with Atlassian's internal APIs to gather the data efficiently.

## Features

* **Automated Login**: Securely logs into `admin.atlassian.com` using credentials from a `.env` file.
* **API-based Data Fetching**: Bypasses traditional web scraping by making direct calls to Atlassian's internal APIs for speed and reliability.
* **Complete User Sync**: Fetches all users in the organization, handling pagination automatically.
* **Complete Group & Membership Sync**: Fetches all groups and subsequently retrieves the full list of members for each group.
* **Data Cross-Referencing**: Processes the collected data to link users to the groups they are a part of.
* **JSON Output**: Saves the final, structured data into two easy-to-use files: `users.json` and `groups.json`.

## Tech Stack

* **Python 3.8+**
* **Playwright**: For browser automation and making authenticated API calls.
* **asyncio**: For managing asynchronous operations.
* **python-dotenv**: For securely managing environment variables.

## Setup and Installation

Follow these steps to set up the project on your local machine.

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Create a Virtual Environment**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    \
   Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright Browsers**
    ```bash
    playwright install
    ```

5.  **Configure Environment Variables**
    Create a file named `.env` in the project's root directory and add your Atlassian credentials and Organization ID:
    ```env
    ATLASSIAN_EMAIL="your-email@example.com"
    ATLASSIAN_PASSWORD="your-secret-password"
    ATLASSIAN_ORG_ID="your_org_id"
    ```

## Usage

To run the main data-fetching script, execute the following command in your terminal:

```bash
python login.py
```

The script will print its progress to the console and, upon successful completion, you will find `users.json` and `groups.json` in your project directory.



# Automating creation of groups and user invitation

This contains a bonus script, `setup.py`, designed to demonstrate the automation of writing data to an Atlassian organization.

## Objective

The goal of this script is to automatically perform administrative setup tasks within Atlassian, specifically:
* Creating new user groups.
* Inviting new users to the organization.
* Assigning those newly invited users to the newly created groups.
```
Initially, the setup.py script was developed to automate the entire prerequisite setup, including the creation of all required users and groups. However, the user invitation feature was blocked by advanced security measures (reCAPTCHA) that could not be automated.

To meet the core requirements of the assessment, I added the necessary users and groups to the Atlassian organization manually. The setup.py script included in this repository was then run to demonstrate the automation capability for the bonus task. In its final state, the script successfully proves the concept by creating new groups, but the user invitation step remains non-functional due to the security challenge.
```
## Approach

The script leverages the **Playwright** library in Python to achieve its goals through a series of automated steps:

1.  **Authentication**: It begins by programmatically logging into the Atlassian admin console to establish an authenticated session. This session provides the necessary cookies and permissions for subsequent actions.

2.  **CSRF Token Retrieval**: After logging in, the script inspects the browser's cookies to find and extract a dynamic Cross-Site Request Forgery (CSRF) token (`atlassian.account.xsrf.token`). This token is a critical security measure required by the Atlassian API for any state-changing requests (like creating a group or user).

3.  **API Interaction via Browser Context**: Instead of making direct HTTP requests from Python (which can be easily blocked by security policies), the script uses a more robust technique. It injects and executes JavaScript `fetch` commands directly within the authenticated browser page using Playwright's `page.evaluate()` method. This ensures that all API calls originate from the browser itself, automatically including all necessary headers and cookies to appear as a legitimate request from the official web application.

4.  **Sequential Operations**:
    * It first calls the group creation endpoint (`.../api/adminhub/um/org/{ORG_ID}/groups`) to create two new groups.
    * It then attempts to call the user invitation endpoint to invite new users.
    * Finally, it would call the group membership endpoint to assign the new users to the new groups.

## Challenges and Final State

During development, the script successfully automated the creation of user groups. However, the user invitation endpoint (`.../users/invite`) is protected by an additional layer of security: **Google reCAPTCHA**.

The server's response `"Missing required recaptcha token."` indicates that this final security check could not be automated. Since reCAPTCHA is specifically designed to distinguish humans from bots, it presents a significant and often insurmountable barrier for standard automation scripts.

As a result, the script in its current state will successfully **create the new groups** but will fail on the step of inviting new users.

## Alternative Approach: `setup2.py` (UI Automation)

As an alternative to the API-based `setup.py` script, this project also includes `setup2.py`, which attempts to automate user and group creation by directly interacting with the website's User Interface (UI).

### Approach

This script uses Playwright to simulate a real user's actions directly in the browser. Instead of intercepting API calls, it performs the following steps:

1.  **Login**: It automates the login process by filling in the email and password fields, just like a user would.
2.  **Navigate**: For each action, it navigates to the appropriate page (e.g., the "Groups" page or the "Users" page). This "hard reset" before each step is designed to ensure the script starts from a known, stable state.
3.  **Simulate Clicks and Keystrokes**: The script finds buttons and input fields on the page using selectors (like `get_by_test_id` or `get_by_role`) and then simulates clicks and keyboard typing to create groups and invite users.
4.  **Wait for UI Feedback**: Instead of waiting for API responses, this script waits for visual cues on the page, such as a success message appearing or an invitation panel disappearing, to confirm that an action was successful.

### Comparison with API-Based Approach

| Feature | API-Based Approach (`setup.py`) | UI-Based Approach (`setup2.py`) |
| :--- | :--- | :--- |
| **Speed** | **Very Fast**. API calls are direct and don't require rendering a webpage. | **Slower**. Must wait for pages, elements, and animations to load. |
| **Stability**| **More Stable**. Less likely to break unless the API endpoints change. | **Less Stable (Brittle)**. Small changes to the website's design, CSS, or `testid`s can break the script. |
| **Security** | Can be blocked by advanced security like reCAPTCHA, as it's harder to prove the request is from a legitimate user session. | Can sometimes bypass simple security, but is more likely to be detected as a bot by services like reCAPTCHA. |
| **Complexity**| Requires finding API endpoints and understanding security tokens (e.g., CSRF). | Requires finding robust selectors for UI elements and managing timing issues. |

### Current Status

The `setup2.py` script is currently **not working as expected**. The primary challenge with this approach is its "brittleness"—it relies on specific selectors and UI flows that can be changed by Atlassian at any time. However, with updated selectors and more robust waiting conditions, this method could be made to work and serves as a valid alternative strategy for automation.


## Script Output

Upon successful execution of `login.py`, the script generates two files in the project's root directory, `users.json` and `groups.json`.

---
### `users.json`

This file contains a list of all user objects found in the Atlassian organization. Each object includes the following fields:

* **id**: The unique `accountId` for the user.
* **name**: The user's full display name.
* **email**: The user's email address.
* **last_active**: A timestamp of the user's last activity, which can be `null`.
* **status**: The current status of the user's account (e.g., "active").
* **groups**: A list of the names of all groups the user is a member of.

**Example:**
```json
[
    {
        "id": "557058:f6e164df-8f7e-4c8b-856a-c72de41acf30",
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "last_active": "2025-09-18T12:00:00.000Z",
        "status": "active",
        "groups": [
            "QA-Testers",
            "confluence-users"
        ]
    }
]
```
---
### `groups.json`

This file contains a list of all group objects found in the organization. Each object includes the following fields:

* **id**: The unique ID for the group.
* **name**: The name of the group.
* **description**: The text description of the group.
* **members**: A list of the display names of all users who are members of the group.

**Example:**
```json
[
    {
        "id": "99bb662e-76df-4905-b57d-23927de52863",
        "name": "QA-Testers",
        "description": "Group for the Quality Assurance team.",
        "members": [
            "Jane Doe",
            "John Smith"
        ]
    }
]
```
