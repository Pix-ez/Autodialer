import csv
import time
import random
import json
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
import os
from dotenv import load_dotenv

#Config

OUTPUT_CSV = "linkedin_profiles_data.csv"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")


CSV_HEADERS = [
    "Profile URL", "About", 
    "Phone", "Email", "Website", "Address", "Birthday", "Twitter"
]
STATE_FILE = "linkedin_state.json"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"


app = FastAPI(title="LinkedIn Scraper API") 

class ScrapeRequest(BaseModel):
    urls: List[str]
    # headless: bool = False  # Option to run headless or not


def save_state(email, password, proxy=None):
    # with sync_playwright() as p:
    with Stealth().use_sync(sync_playwright()) as p:
       
        browser = p.chromium.launch(headless=False)
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            # proxy={"server": proxy}
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
        time.sleep(10)
 
        
        print("Waiting for successful login (checking for Feed URL)...")
        
  
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
    # stealth_sync(page)
    return browser, context, page

def extract_about_section(page):
    try:
        about_heading = page.locator("h2", has_text="About").first
        if not about_heading.is_visible():
            return "N/A"
            
        about_section = about_heading.locator("xpath=./ancestor::section").first
        
        # Expand text if needed
        see_more = about_section.locator("button.inline-show-more-text__button")
        if see_more.count() > 0 and see_more.is_visible():
            see_more.click()
            time.sleep(0.5)

        full_text = about_section.text_content().strip()
        cleaned_text = full_text
        
        # Cleanup
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
        
        # Wait for modal
        modal = page.get_by_role("dialog").filter(has_text="Contact info")
        modal.wait_for(state="visible", timeout=8000)
        
        # Wait for content to load
        try:
            modal.locator("section.pv-contact-info__contact-type").first.wait_for(state="visible", timeout=5000)
        except:
            time.sleep(2) # Fallback

        # Scrape specific fields ["Website", "Phone", "Email", "Birthday", "Address"]
        labels_to_find = ["Website", "Phone", "Email", "Birthday", "Address", "Twitter"]
        for label in labels_to_find:
            # XPath to find label and grab the sibling following it
            locator = modal.locator(f"xpath=//p[normalize-space()='{label}']/following-sibling::*").first
            if locator.is_visible():
                value = locator.text_content().strip()
                value = " ".join(value.split()) # Remove extra whitespace
                contact_data[label] = value

        # Close modal
        page.keyboard.press("Escape")
        modal.wait_for(state="hidden", timeout=5000)
        
    except Exception as e:
        print(f"   -> Error in contact info: {e}")
        page.keyboard.press("Escape")
        
    return contact_data

def process_single_profile(page, url):

    print(f"Processing: {url}")
    row_data = {
        "Profile URL": url,
        "About": "N/A"
    }
    
    try:
        page.goto(url)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeout:
            pass # Continue even if network is busy

        # Random sleep + scroll for lazy loading
        time.sleep(random.uniform(3, 5))
        page.mouse.wheel(0, 800)
        time.sleep(1)
        page.mouse.wheel(0, 800)
        time.sleep(1)
        page.keyboard.press("Home")
        time.sleep(1)

        # 1. Get About
        row_data["About"] = extract_about_section(page)

        # 2. Get Contact Info
        contact_details = extract_contact_info(page)
        
        # Merge contact details into the main row dictionary
        # This maps "Email" from contact_details to "Email" in CSV columns
        row_data.update(contact_details)

    except Exception as e:
        print(f"CRITICAL ERROR on {url}: {e}")
    
    return row_data



def run_batch_scraper(url_list, proxy=None):
    with sync_playwright() as p:
        # 1. Start Browser (Once for the whole list)
        browser, context, page = setup_browser(p, proxy=proxy, headless=False)
        
        # 2. Open CSV file
        # 'w' mode to overwrite, 'a' to append. 
        # newline='' is required by the csv module
        with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS, extrasaction='ignore')
            writer.writeheader()
            
            total = len(url_list)
            print(f"Starting batch scrape for {total} profiles...")

            # 3. Loop through URLs
            for index, url in enumerate(url_list):
                print(f"\n[{index + 1}/{total}] --------------------------------")
                
                data = process_single_profile(page, url)
                
                # Write to CSV immediately (so data is saved if script crashes)
                writer.writerow(data)
                print(f"Saved data for: {url}")

                # 4. SAFETY SLEEP (Crucial!)
                # Sleep between 10 to 20 seconds between profiles
                if index < total - 1:
                    sleep_time = random.uniform(10, 20)
                    print(f"Sleeping for {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)

        print("\nBatch scraping complete!")
        browser.close()


@app.get("/")
def health_check():
    return {"status": "active", "message": "LinkedIn Scraper API is running"}

@app.post("/scrape")
def scrape_profiles(request: ScrapeRequest):
    """
    Accepts a list of URLs, loops through them, and returns nested JSON data.
    """
    if not os.path.exists(STATE_FILE):
        raise HTTPException(status_code=400, detail=f"State file '{STATE_FILE}' not found. Please use login first.")

    results = []
    
    # We use sync_playwright inside a standard def function.
    # FastAPI runs this in a threadpool, so it doesn't block the server heartbeat completely.
    # with sync_playwright() as p:
    with Stealth().use_sync(sync_playwright()) as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=False)
        
        context = browser.new_context(
            storage_state=STATE_FILE,
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        total = len(request.urls)
        
        for index, url in enumerate(request.urls):
            print(f"[{index + 1}/{total}] Scraping {url}")
            
            data = process_single_profile(page, url)
            
            # Structure the nested JSON output
            user_record = {
                "url": url,
                "scraped_data": data
            }
            results.append(user_record)

            # Safety sleep between profiles if there are more to go
            if index < total - 1:
                sleep_time = random.uniform(5, 10) # Reduced slightly for API responsiveness
                print(f"Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

        browser.close()

    return {"count": len(results), "profiles": results}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)