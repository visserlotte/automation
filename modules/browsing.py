# ~/automation/modules/browsing.py
from playwright.sync_api import sync_playwright


def fetch_page_content(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        content = page.content()
        browser.close()
        return content[:2000]  # Limit response length for safety
