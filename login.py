# Import necessary libraries
import os  # Used for accessing environment variables
import json  # Used for handling JSON data (reading/writing files)
from playwright.async_api import async_playwright  # The main library for browser automation
from dotenv import load_dotenv  # Used to load credentials from a .env file
import asyncio  # The library for running asynchronous Python code

# Load environment variables from a .env file in the same directory
load_dotenv()

# --- Configuration ---
# Retrieve Atlassian credentials and Organization ID from environment variables
# This is a secure way to handle sensitive data without hardcoding it in the script.
ATLASSIAN_EMAIL = os.getenv("ATLASSIAN_EMAIL")
ATLASSIAN_PASSWORD = os.getenv("ATLASSIAN_PASSWORD")
ORG_ID = "e487b234-1e3a-4c58-b4b2-1343fcb828b8" 
BASE_URL = f"https://admin.atlassian.com/o/{ORG_ID}/"

async def login(page):
    """
    Automates the login process for the Atlassian admin console.
    It navigates to the login page, enters credentials, and waits for a successful login.
    """
    print("Navigating to login page...")
    await page.goto("https://admin.atlassian.com")
    
    # Locate the email input field, wait for it to be ready, and fill it
    await page.wait_for_selector('input[name="username"]')
    await page.locator('input[name="username"]').fill(ATLASSIAN_EMAIL)
    await page.locator('button[id="login-submit"]').click()
    
    # After submitting the email, locate the password field, wait, and fill it
    await page.wait_for_selector('input[name="password"]')
    await page.locator('input[name="password"]').fill(ATLASSIAN_PASSWORD)
    await page.locator('button[id="login-submit"]').click()
    
    print("Login successful! Waiting for dashboard to load...")
    # To confirm a successful login, wait for a specific, stable element on the dashboard page.
    # This ensures the page is fully loaded before the script proceeds.
    await page.wait_for_selector('span:has-text("sample overview")')
    print("Successfully logged in.")

async def fetch_users(page):
    """
    Fetches all user accounts from the Atlassian organization by making direct API calls.
    [cite_start]This method is preferred over web scraping as it's faster and more reliable. [cite: 33]
    [cite_start]It also handles pagination to ensure all users are retrieved. [cite: 10]
    """
    print("Fetching all users...")
    all_users = []
    
    # This is the specific API endpoint for fetching user data.
    # Using a high limit reduces the number of required API calls.
    next_url = f"https://admin.atlassian.com/gateway/api/admin/v2/orgs/{ORG_ID}/directories/-/users?limit=100"

    # Loop as long as the API response provides a 'next' link for the next page of results.
    while next_url:
        print(f"Fetching from: {next_url}")
        # Use the page's authenticated context to make the GET request.
        # This automatically includes the necessary login cookies.
        api_response = await page.request.get(next_url)
        data = await api_response.json()
        
        # Extend our list of users with the users found on the current page.
        all_users.extend(data.get("data", []))
        
        # Get the URL for the next page from the 'links' object in the response.
        # If there is no 'next' link, the value will be None, and the loop will terminate.
        next_url = data.get("links", {}).get("next", None)

    print(f"✅ Total users fetched: {len(all_users)}")
    return all_users

async def fetch_group_members(page, group_id):
    """
    For a given group ID, fetches all members belonging to that group.
    This function also handles pagination for groups that have a large number of members.
    """
    all_members = []
    start_index = 1
    count = 50 # Fetch members in batches of 50

    # This loop continues until a page with no members is returned, indicating the end.
    while True:
        # This is the specific API endpoint for fetching members of a particular group.
        url = f"https://admin.atlassian.com/gateway/api/adminhub/um/org/{ORG_ID}/groups/{group_id}/members?count={count}&start-index={start_index}"
        response = await page.request.get(url)
        data = await response.json()
        
        # The API response for members nests the list under the "users" key.
        members_on_page = data.get("users", [])
        
        # If the list of members on the current page is empty, we've fetched everyone.
        if not members_on_page:
            break
        
        all_members.extend(members_on_page)
        # Increment the start_index for the next page request.
        start_index += count
    
    return all_members

async def fetch_groups(page):
    """
    Fetches all groups in the organization and then fetches the members for each group.
    It first gets a list of all groups and then iterates through them to populate their member lists.
    """
    print("Fetching all groups...")
    all_groups = []
    start_index = 1 # Atlassian's group API is 1-indexed.
    count = 20 # Fetch groups in batches of 20.

    # Loop until a page with no groups is returned.
    while True:
        # The API endpoint for fetching the list of groups.
        url = f"https://admin.atlassian.com/gateway/api/adminhub/um/org/{ORG_ID}/groups?count={count}&start-index={start_index}"
        print(f"Fetching groups list from: {url}")
        
        api_response = await page.request.get(url)
        data = await api_response.json()
        
        # The API response for groups nests the list under the "groups" key.
        groups_on_page = data.get("groups", [])
            
        if not groups_on_page:
            break
        
        # For each group found, call the helper function to fetch its members.
        for group in groups_on_page:
            print(f"---> Fetching members for group: {group['name']}")
            members = await fetch_group_members(page, group['id'])
            # Add the fetched list of members as a new key to the group object.
            group['members'] = members

        all_groups.extend(groups_on_page)
        # Increment the start_index for the next page of groups.
        start_index += count

    print(f"✅ Total groups fetched: {len(all_groups)}")
    return all_groups

def save_to_json(users_data, groups_data):
    """
    [cite_start]Processes the raw user and group data to create two final JSON files. [cite: 11]
    It cross-references the data to link users to their groups and vice-versa,
    and formats the output with readable names as requested.
    """
    print("Finalizing and saving data with readable names...")

    # --- Step 1: Create a lookup map for users ---
    # This dictionary will map a user's ID to a list of group names they belong to.
    # The user ID from the main user list is under the 'accountId' key.
    user_to_groups_map = {
        user.get("accountId"): [] for user in users_data if user.get("accountId")
    }

    # --- Step 2: Populate the map with group memberships ---
    # Iterate through each group and its members to build the relationship.
    for group in groups_data:
        group_name = group.get("name")
        for member in group.get('members', []):
            # The member object from the member list uses the key 'id' for the user's accountId.
            member_id = member.get('id') 
            # If the member's ID exists in our user map, add the group name to their list.
            if member_id in user_to_groups_map:
                user_to_groups_map[member_id].append(group_name)

    # --- Step 3: Generate and save users.json ---
    # [cite_start]Format the user data according to the assessment requirements. [cite: 12]
    users_output = [
        {
            "id": user.get("accountId"),
            "name": user.get("name"),
            "email": user.get("email"),
            "last_active": user.get("last_active_date"),
            "status": user.get("status"),
            # Get the list of group names for this user from the map we created.
            "groups": user_to_groups_map.get(user.get("accountId"), [])
        }
        for user in users_data
    ]
    with open("users.json", "w") as f:
        json.dump(users_output, f, indent=4)
    print("Saved users.json")

    # --- Step 4: Generate and save groups.json ---
    # [cite_start]Format the group data according to the assessment requirements. [cite: 20]
    groups_output = [
        {
            "id": group.get("id"),
            "name": group.get("name"),
            "description": group.get("description"),
            # The member object from the API includes the user's name under 'displayName'.
            "members": [member.get('displayName') for member in group.get('members', [])]
        }
        for group in groups_data
    ]
    with open("groups.json", "w") as f:
        json.dump(groups_output, f, indent=4)
    print("Saved groups.json")

async def main():
    """The main function that orchestrates the entire automation process."""
    # Use async with to ensure the Playwright browser is always closed properly.
    async with async_playwright() as p:
        # Launch the browser. Set headless=False to watch the script in action.
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # The script executes the main steps in sequence.
            await login(page)
            
            # Fetch all user and group data from the Atlassian APIs.
            users = await fetch_users(page)
            groups = await fetch_groups(page)
            
            # Process and save the collected data into the final JSON files.
            save_to_json(users, groups)
            
            print("\n🎉 Script finished successfully!")

        except Exception as e:
            # Basic error handling to catch any exceptions during the run.
            print(f"An error occurred: {e}")
        finally:
            # Ensure the browser is closed even if an error occurs.
            await browser.close()

# This is the standard entry point for a Python script.
if __name__ == "__main__":
    # asyncio.run() starts the execution of our async main function.
    asyncio.run(main())