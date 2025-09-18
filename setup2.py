import asyncio
import os
from playwright.async_api import async_playwright, expect
from dotenv import load_dotenv

# --- Configuration ---
# You can change these details as needed
NEW_GROUPS = [
    {"name": "Alpha Team", "description": "Primary development team."},
    {"name": "Bravo Team", "description": "Secondary support team."}
]
NEW_USERS = [
    {"email": f"alpha.user1@example.com", "group_name": "Alpha Team"},
    {"email": f"bravo.user1@example.com", "group_name": "Bravo Team"}
]

class AtlassianSetup:
    """
    Automates creating new groups and inviting new users to them in Atlassian.
    """

    def __init__(self, email: str, password: str, org_id: str, headless: bool = True):
        self.email = email
        self.password = password
        self.org_id = org_id
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self):
        """Automates the Atlassian login process."""
        print("Navigating to login page...")
        await self.page.goto("https://admin.atlassian.com")
        
        print("Entering email...")
        await self.page.get_by_placeholder("Enter your email").fill(self.email)
        await self.page.get_by_role("button", name="Continue").click()
        
        print("Entering password...")
        await self.page.get_by_placeholder("Enter password").fill(self.password)
        await self.page.get_by_role("button", name="Log in").click()
        
        await self.page.wait_for_url(f"**/{self.org_id}/**", timeout=30000)
        print("✅ Login successful.")

    async def create_groups(self):
        """Creates the new groups defined in the configuration."""
        print("\n--- Starting to create groups ---")
        for group in NEW_GROUPS:
            group_name = group["name"]
            group_description = group["description"]
            print(f"Creating group: '{group_name}'...")
            try:
                # Start fresh on the groups page for each creation
                await self.page.goto(f"https://admin.atlassian.com/o/{self.org_id}/groups")

                await self.page.get_by_test_id("admin-teams-card-list-view.ui.admin-teams-create-team-button").click()
                
                await self.page.get_by_test_id("admin-teams-team-profile-card.ui.form.textfield-name").fill(group_name)
                await self.page.get_by_test_id("admin-teams-team-profile-card.ui.form.textarea-description").fill(group_description)
                await self.page.get_by_test_id("admin-teams-team-create-form.ui.create-button").click()

                # Wait for the success message to confirm creation
                await expect(self.page.get_by_text(f"You created {group_name}")).to_be_visible(timeout=10000)
                print(f"✅ Successfully created group '{group_name}'.")

            except Exception as e:
                print(f"❌ Could not create group '{group_name}'. Error: {e}")
                await self.page.screenshot(path=f"error_creating_{group_name.replace(' ', '_')}.png")


    async def invite_users(self):
        """Invites new users and assigns them to their respective new groups."""
        print(f"\n--- Starting to invite users ---")
        for user in NEW_USERS:
            user_email = user["email"]
            group_name_to_assign = user["group_name"]
            print(f"Inviting '{user_email}' to group '{group_name_to_assign}'...")
            
            try:
                # Start fresh on the users page for each invitation
                await self.page.goto(f"https://admin.atlassian.com/o/{self.org_id}/users")
                
                await self.page.get_by_test_id("nav-invite-users").click()
                
                email_input_container = self.page.locator('[data-testid*="invitee-list-user-picker-paste-handler"]')
                await email_input_container.click()
                await self.page.keyboard.type(user_email)
                await self.page.keyboard.press("Enter")
                
                await self.page.wait_for_timeout(1000) # Short pause for UI to update
                
                group_input = self.page.get_by_text("Add groups (optional)")
                await group_input.click()
                await self.page.keyboard.type(group_name_to_assign)
                
                await self.page.get_by_text(group_name_to_assign, exact=True).first.click()

                send_invite_button = self.page.get_by_test_id("invite-submit-button")
                await send_invite_button.click()
                
                # Wait for the invitation panel to close
                await expect(self.page.get_by_test_id("invite-drawer-component")).to_be_hidden(timeout=15000)
                print(f"✅ Successfully sent invitation to '{user_email}'.")
                
            except Exception as e:
                print(f"❌ Could not invite '{user_email}'. Error: {e}")
                await self.page.screenshot(path=f"error_inviting_{user_email}.png")

async def main():
    load_dotenv()
    email = os.getenv("ATLASSIAN_EMAIL")
    password = os.getenv("ATLASSIAN_PASSWORD")
    org_id = os.getenv("ATLASSIAN_ORG_ID")

    if not all([email, password, org_id]):
        raise ValueError("Please set ATLASSIAN_EMAIL, ATLASSIAN_PASSWORD, and ATLASSIAN_ORG_ID in your .env file.")
    
    async with AtlassianSetup(email, password, org_id, headless=False) as setup:
        try:
            await setup.login()
            await setup.create_groups()
            await setup.invite_users()
            print("\n✅ Setup complete! All groups and users have been created.")
        except Exception as e:
            print(f"\n❌ An error occurred during the main setup process: {e}")
            await setup.page.screenshot(path="main_error_screenshot.png")

if __name__ == "__main__":
    asyncio.run(main())