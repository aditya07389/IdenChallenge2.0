import os
import json
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from urllib.parse import quote

# --- Configuration ---
load_dotenv()
ATLASSIAN_EMAIL = os.getenv("ATLASSIAN_EMAIL")
ATLASSIAN_PASSWORD = os.getenv("ATLASSIAN_PASSWORD")
ORG_ID = "e487b234-1e3a-4c58-b4b2-1343fcb828b8"

# --- Data for new groups and users ---
GROUPS_TO_CREATE = [
    {"name": "DevOps Team", "description": "Group for DevOps engineers."},
    {"name": "QA-Testers", "description": "Group for the Quality Assurance team."}
]
USERS_TO_INVITE = [
    # Using new emails to avoid conflicts with previously created users
    {"email": "devops-final@example.com", "group_name": "DevOps Team"},
    {"email": "qa-final@example.com", "group_name": "QA-Testers"}
]

# --- Reusable Login Function ---
async def login(page):
    """Logs into the Atlassian admin console."""
    print("Navigating to login page...")
    await page.goto("https://admin.atlassian.com")
    await page.wait_for_selector('input[name="username"]')
    await page.locator('input[name="username"]').fill(ATLASSIAN_EMAIL)
    await page.locator('button[id="login-submit"]').click()
    await page.wait_for_selector('input[name="password"]')
    await page.locator('input[name="password"]').fill(ATLASSIAN_PASSWORD)
    await page.locator('button[id="login-submit"]').click()
    print("Login successful! Waiting for dashboard to load...")
    await page.wait_for_selector('span:has-text("sample overview")')
    print("✅ Successfully logged in.")

# --- Function to get the CSRF token ---
async def get_csrf_token(page):
    """Finds the atlassian.account.xsrf.token from the browser cookies."""
    await page.wait_for_timeout(2000)
    cookies = await page.context.cookies()
    correct_cookie_name = "atlassian.account.xsrf.token"
    
    for cookie in cookies:
        if cookie['name'] == correct_cookie_name:
            token = cookie['value']
            print(f"✅ Found CSRF Token: {token}")
            return token
            
    print(f"❌ ERROR: Could not find the required cookie: '{correct_cookie_name}'.")
    return None

# --- API Helper Functions (with the final correct invite_user URL) ---
async def create_group(page, name, description, csrf_token):
    """Creates a group by executing a fetch call directly in the browser context."""
    print(f"Attempting to create group: '{name}'...")
    url = f"https://admin.atlassian.com/gateway/api/adminhub/um/org/{ORG_ID}/groups"
    payload = {"name": name, "description": description}
    
    result = await page.evaluate("""
        async ({ url, payload, csrf_token }) => {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'atl-token': csrf_token },
                body: JSON.stringify(payload)
            });
            if (!response.ok) return { error: true, status: response.status, text: await response.text() };
            return await response.json();
        }
    """, {"url": url, "payload": payload, "csrf_token": csrf_token})

    if result.get("error"):
        print(f"  -> ERROR: Failed to create group '{name}'. Status: {result['status']}, Response: {result['text']}")
        return None
    else:
        group_id = result.get("id")
        print(f"  -> SUCCESS: Created group '{name}' with ID: {group_id}")
        return group_id

async def invite_user(page, email, csrf_token):
    """Invites a user and then finds their account ID."""
    print(f"Attempting to invite user: '{email}'...")
    
    # STEP 1: Send the invitation via the correct /users/invite endpoint.
    invite_url = f"https://admin.atlassian.com/gateway/api/adminhub/um/org/{ORG_ID}/users/invite"
    invite_payload = {"emails": [email]}
    
    invite_result = await page.evaluate("""
        async ({ url, payload, csrf_token }) => {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'atl-token': csrf_token },
                body: JSON.stringify(payload)
            });
            const responseText = await response.text();
            return { ok: response.ok, status: response.status, text: responseText };
        }
    """, {"url": invite_url, "payload": invite_payload, "csrf_token": csrf_token})

    if not invite_result.get("ok"):
        print(f"  -> ERROR: Failed to send invite for '{email}'. Status: {invite_result['status']}, Response: {invite_result['text']}")
        return None
    
    print(f"  -> SUCCESS: Invite sent for '{email}'. Now finding user's accountId...")
    await page.wait_for_timeout(3000) # Give the system a moment to process the invite.
    
    # STEP 2: Find the user using the /v2/directories/users endpoint which we know works for searching.
    encoded_email = quote(email)
    search_url = f"https://admin.atlassian.com/gateway/api/admin/v2/orgs/{ORG_ID}/directories/-/users?filter=email%20eq%20%22{encoded_email}%22"
    
    search_response = await page.request.get(search_url)
    if not search_response.ok:
        print(f"  -> ERROR: Could not search for user '{email}' after inviting. Status: {search_response.status}")
        return None
        
    search_data = await search_response.json()
    users_found = search_data.get("data", [])
    if not users_found:
        print(f"  -> ERROR: User '{email}' not found after invite. They may need to accept the invitation first.")
        return None
        
    user_id = users_found[0].get("account_id")
    print(f"  -> SUCCESS: Found Account ID: {user_id}")
    return user_id

async def add_user_to_group(page, group_id, user_id, csrf_token):
    """Adds a user to a group by executing a fetch call directly in the browser context."""
    print(f"Attempting to add user {user_id} to group {group_id}...")
    url = f"https://admin.atlassian.com/gateway/api/adminhub/um/org/{ORG_ID}/groups/{group_id}/members"
    payload = {"accountIds": [user_id]}
    
    result = await page.evaluate("""
        async ({ url, payload, csrf_token }) => {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'atl-token': csrf_token },
                body: JSON.stringify(payload)
            });
            if (!response.ok) return { error: true, status: response.status, text: await response.text() };
            return { success: true }; 
        }
    """, {"url": url, "payload": payload, "csrf_token": csrf_token})
    
    if result.get("success"):
        print(f"  -> SUCCESS: User added to group.")
        return True
    else:
        print(f"  -> ERROR: Failed to add user to group. Status: {result['status']}, Response: {result['text']}")
        return False

# --- Main Orchestration Function ---
async def main():
    """Runs the setup process."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await login(page)
            
            csrf_token = await get_csrf_token(page)
            if not csrf_token:
                print("Aborting script because CSRF token could not be found.")
                return

            group_id_map = {}
            for group in GROUPS_TO_CREATE:
                group_id = await create_group(page, group["name"], group["description"], csrf_token)
                if group_id:
                    group_id_map[group["name"]] = group_id
            
            for user_info in USERS_TO_INVITE:
                user_id = await invite_user(page, user_info["email"], csrf_token)
                if user_id:
                    target_group_name = user_info["group_name"]
                    target_group_id = group_id_map.get(target_group_name)
                    if target_group_id:
                        await add_user_to_group(page, target_group_id, user_id, csrf_token)
                    else:
                        print(f"  -> WARNING: Could not find group '{target_group_name}' to assign user to.")

            print("\n🎉 Setup script finished successfully!")

        except Exception as e:
            print(f"A critical error occurred: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())