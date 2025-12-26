import hashlib
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from feedgen.feed import FeedGenerator

# Detect manual run from GitHub Actions
manual_run = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

URL = "https://sta-russell.cdsbeo.on.ca/apps/news/"
HASH_FILE = "data/last_hash.txt"

def normalize(text: str) -> str:
    return " ".join(text.split())

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# Ensure data folder exists
os.makedirs("data", exist_ok=True)

# Fetch content
res = requests.get(
    URL,
    headers={"User-Agent": "RSS-Monitor/1.0"},
    timeout=15
)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

# Target main content if available
main = soup.find("main")
content = normalize(main.get_text()) if main else normalize(soup.get_text())

# Compute content hash
new_hash = hash_content(content)
old_hash = None

if os.path.exists(HASH_FILE):
    old_hash = open(HASH_FILE).read().strip()

# Skip update if unchanged and not a manual run
if new_hash == old_hash and not manual_run:
    print("No change detected")
    exit(0)

print("Updating RSS feed...")

# Save hash only on scheduled runs
if not manual_run:
    with open(HASH_FILE, "w") as f:
        f.write(new_hash)

# Create RSS feed
fg = FeedGenerator()
fg.title("Change Monitor Feed")
fg.link(href="https://dustindoucette.github.io/Demo-RSS-Feed", rel="alternate")
fg.link(href="https://dustindoucette.github.io/Demo-RSS-Feed/rss.xml", rel="self", type="application/rss+xml")
fg.description("Updates only when content changes")

# Add entry
fe = fg.add_entry()
fe.title("Content Updated")
fe.link(href=URL)
fe.description(f"<![CDATA[{content[:1000]}…]]>")  # wrap in CDATA for special characters
fe.pubDate(datetime.now(ZoneInfo("America/Toronto")))
fe.guid(new_hash, permalink=False)  # unique identifier

# Write RSS file to root (for GitHub Pages)
fg.rss_file("rss.xml")
