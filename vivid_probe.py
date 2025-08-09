import logging
import os
import random
import sys
import time

import requests
from bs4 import BeautifulSoup

# ─── SETTINGS ────────────────────────────────────────────────────────────
API_KEY = "e401c87a31a45c9ef0f7b709e8af3efa"  # ScraperAPI key
TARGET_URL = "https://www.vividseats.com/concerts/"
MAX_TITLES = 10  # how many titles to print / log
LOG_FILE = "scraped_titles.log"
# ─────────────────────────────────────────────────────────────────────────

# create log dir if missing
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/vivid_probe.log",
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)


def human_delay(a=1.2, b=3.4):
    """Sleep a random human-like amount of time (seconds)."""
    time.sleep(random.uniform(a, b))


def fetch_page(url: str) -> str:
    """Fetch a page through ScraperAPI (single-endpoint mode)."""
    params = {
        "api_key": API_KEY,
        "url": url,
        "render": "true",  # let ScraperAPI handle JavaScript
    }
    try:
        r = requests.get("https://api.scraperapi.com", params=params, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logging.error(f"Fetch failed: {e}")
        sys.exit("[❌] Scrape failed – see logs")


def parse_titles(html: str):
    """Return list of <h3> titles found."""
    soup = BeautifulSoup(html, "html.parser")
    titles = [h.get_text(strip=True) for h in soup.find_all("h3")]
    return titles


# ─── MAIN ────────────────────────────────────────────────────────────────
print("🔍 Fetching page via ScraperAPI …")
html = fetch_page(TARGET_URL)
human_delay()

titles = parse_titles(html)

if titles:
    print("✅  Event titles found:")
    for t in titles[:MAX_TITLES]:
        print("   •", t)
        with open(LOG_FILE, "a") as f:
            f.write(t + "\n")
    logging.info(f"Successfully scraped {len(titles)} titles")
else:
    print("⚠️  No <h3> titles found on page")
    logging.warning("No titles parsed – check target URL / parser rules")
