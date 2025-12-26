import hashlib
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from feedgen.feed import FeedGenerator

# GitHub Actions environment variable to detect manual run
manual_run = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

URL = "https://sta-russell.cdsbeo.on.ca/apps/news/"
HASH_FILE = "data/last_hash.txt"

def normalize(text: str) -> str:
    return " ".join(text.split())

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

os.makedirs("data", exist_ok=True)

res = requests.get(
    URL,
    headers={"User-Agent": "RSS-Monitor/1.0"},
    timeout=15
)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

# 🔑 target stable content only
main = soup.find("main")
content = normalize(main.get_text()) if main else normalize(soup.get_text())

new_hash = hash_content(content)
old_hash = None

if os.path.exists(HASH_FILE):
    old_hash = open(HASH_FILE).read().strip()

# Only skip update if content is unchanged AND this is not a manual run
if new_hash == old_hash and not manual_run:
    print("No change detected")
    exit(0)

print("Updating RSS feed...")

# Save new hash only on scheduled runs (optional: avoids affecting change detection)
if not manual_run:
    with open(HASH_FILE, "w") as f:
        f.write(new_hash)

# Create or update RSS feed
fg = FeedGenerator()
fg.title("Change Monitor Feed")
fg.link(href="https://dustindoucette.github.io/Demo-RSS-Feed", rel="alternate")
fg.description("Updates only when content changes")

fe = fg.add_entry()
fe.title("Content Updated")
fe.link(href=URL)
fe.description(content[:1000] + "…")
fe.pubDate(datetime.now(ZoneInfo("America/Toronto")))

# Write RSS to repo root for GitHub Pages
fg.rss_file("rss.xml")
