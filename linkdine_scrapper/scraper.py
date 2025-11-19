import time
import random
import json  # Added json library
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
import os
from dotenv import load_dotenv

# --- CONFIG ---
OUTPUT_JSON = "linkedin_profiles_data.json" # Changed to JSON
INPUT_FILE = "profile_url.txt"
STATE_FILE = "linkedin_state.json"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")

def save_state(email, password, proxy=None):
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=False)
        
        context = browser.new_context(
            user_agent=USER_AGENT,
        )

        page = context.new_page()
        page.set_default_navigation_timeout(10000)
        page.set_default_timeout(10000)

        print(f"Navigating to {LINKEDIN_LOGIN_URL}...")
        page.goto(LINKEDIN_LOGIN_URL)

        page.fill("input#username", email)
        page.fill("input#password", password)
        print("Credentials filled. Clicking submit...")
        page.click("button[type=submit]")
        
        # Wait long enough for manual captcha if needed
        time.sleep(15)
 
        print("Saving state...")
        context.storage_state(path=STATE_FILE)
        print(f"SUCCESS! State saved to '{STATE_FILE}'.")

        browser.close()

def setup_browser(p, proxy=None, headless=False):
    print("Launching browser...")
    browser = p.chromium.launch(headless=headless)
    
    context_args = {
        "storage_state": STATE_FILE,
        "user_agent": USER_AGENT,
        "viewport": {"width": 1280, "height": 720}
    }
    
    if proxy:
        context_args["proxy"] = {"server": proxy}

    context = browser.new_context(**context_args)
    page = context.new_page()
    return browser, context, page

def extract_about_section(page):
    try:
        about_heading = page.locator("h2", has_text="About").first
        if not about_heading.is_visible():
            return "N/A"
            
        about_section = about_heading.locator("xpath=./ancestor::section").first
        
        see_more = about_section.locator("button.inline-show-more-text__button")
        if see_more.count() > 0 and see_more.is_visible():
            see_more.click()
            time.sleep(0.5)

        full_text = about_section.text_content().strip()
        cleaned_text = full_text
        
        if cleaned_text.startswith("About"):
            cleaned_text = cleaned_text[5:].strip()
        if "see more" in cleaned_text.lower():
            cleaned_text = cleaned_text.replace("...see more", "").replace("see more", "").strip()
            
        return cleaned_text.strip()
    except Exception:
        return "Error"

def extract_contact_info(page):
    contact_data = {}
    try:
        contact_link = page.locator("a", has_text="Contact info").first
        if not contact_link.is_visible():
            return contact_data

        contact_link.click()
        
        modal = page.get_by_role("dialog").filter(has_text="Contact info")
        modal.wait_for(state="visible", timeout=8000)
        
        try:
            modal.locator("section.pv-contact-info__contact-type").first.wait_for(state="visible", timeout=5000)
        except:
            time.sleep(2)

        labels_to_find = ["Website", "Phone", "Email", "Birthday", "Address", "Twitter"]
        for label in labels_to_find:
            locator = modal.locator(f"xpath=//p[normalize-space()='{label}']/following-sibling::*").first
            if locator.is_visible():
                value = locator.text_content().strip()
                value = " ".join(value.split())
                contact_data[label] = value

        page.keyboard.press("Escape")
        modal.wait_for(state="hidden", timeout=5000)
        
    except Exception as e:
        print(f"   -> Error in contact info: {e}")
        page.keyboard.press("Escape")
        
    return contact_data

def process_single_profile(page, url):
    """Orchestrates the scraping for one URL and returns nested dict."""
    print(f"Processing: {url}")
    
    # Basic structure
    profile_data = {
        "url": url,
        "about": "N/A",
        "contact_details": {}
    }
    
    try:
        page.goto(url)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeout:
            pass 

        time.sleep(random.uniform(3, 5))
        page.mouse.wheel(0, 800)
        time.sleep(1)
        page.mouse.wheel(0, 800)
        time.sleep(1)
        page.keyboard.press("Home")
        time.sleep(1)

        # 1. Get About
        profile_data["about"] = extract_about_section(page)

        # 2. Get Contact Info (Nested)
        profile_data["contact_details"] = extract_contact_info(page)

    except Exception as e:
        print(f"CRITICAL ERROR on {url}: {e}")
        profile_data["error"] = str(e)
    
    return profile_data


def run_batch_scraper(url_list, proxy=None):
    results = [] # Store all profiles here

    with sync_playwright() as p:
        browser, context, page = setup_browser(p, proxy=proxy, headless=False)
        
        total = len(url_list)
        print(f"Starting batch scrape for {total} profiles...")

        for index, url in enumerate(url_list):
            print(f"\n[{index + 1}/{total}] --------------------------------")
            
            # Clean URL in case of whitespace
            url = url.strip()
            if not url: continue

            data = process_single_profile(page, url)
            results.append(data)
            
            print(f"Data collected for: {url}")

            # Safety Sleep
            if index < total - 1:
                sleep_time = random.uniform(10, 20)
                print(f"Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

        browser.close()
    
    # Save to JSON file
    print(f"\nWriting results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print("Done!")



if __name__ == "__main__":
    load_dotenv()
    
    dummy_email = os.getenv("EMAIL")
    dummy_password = os.getenv("PASSWORD") 
    my_proxy = None

    # 1. Check for state file, login if needed
    if not os.path.exists(STATE_FILE):
        print("State file not found. Logging in first...")
        save_state(dummy_email, dummy_password, proxy=my_proxy)

    # 2. Read URLs from text file
    target_urls = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            # Split by comma, strip whitespace
            target_urls = [u.strip() for u in content.split(",") if u.strip()]
    else:
        print(f"Error: {INPUT_FILE} not found. Please create it with comma-separated URLs.")
        exit()

    if not target_urls:
        print("No URLs found in the text file.")
    else:
        run_batch_scraper(target_urls, proxy=my_proxy)