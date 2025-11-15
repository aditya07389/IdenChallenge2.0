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




```
