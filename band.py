import json
import os
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables from .env file (if present)
load_dotenv()

# Get Webhook URL from environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://www.band.us/band/67130116/post"
OUTPUT_FILE = "infinite_scroll_posts.json"
USER_DATA_DIR = os.path.abspath("./chrome_user_data")
INITIAL_FLAG_FILE = "session_initialized.flag"

MAX_INITIAL_SCROLLS = 15
SCROLL_DELAY = 2500
POLL_INTERVAL = 60
FIRST_RUN_WAIT_TIME = 600  # 10 minutes wait on first run

URL_FILTER = "get_posts"
captured_json = []
processed_post_keys = set()


def send_to_discord(title, content, post_url=""):
    if not DISCORD_WEBHOOK_URL or "discord.com" not in DISCORD_WEBHOOK_URL:
        print("[Discord Warning] DISCORD_WEBHOOK_URL is not set or invalid.")
        return

    embed = {
        "title": title[:256],
        "description": content[:2000] if content else "No text content",
        "url": post_url if post_url else TARGET_URL,
        "color": 5814783,
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=10)
    except Exception as e:
        print(f"[Discord Error] {e}")


def extract_and_send_posts(data):
    result_data = data.get("result_data", {})
    items = result_data.get("items", []) if isinstance(result_data, dict) else []

    if not items and isinstance(data, dict) and "items" in data:
        items = data.get("items", [])

    for item in items:
        if not isinstance(item, dict):
            continue
        post_key = item.get("post_key") or item.get("id")
        if post_key and post_key not in processed_post_keys:
            processed_post_keys.add(post_key)
            content = item.get("content", "") or item.get("body", "")
            author = item.get("author", {}).get("name", "Unknown Author")
            post_url = f"https://www.band.us/band/67130116/post/{post_key}"
            send_to_discord(f"New Band Post by {author}", content, post_url)


def handle_response(response):
    url = response.url
    content_type = response.headers.get("content-type", "")

    if "sentry" in url or "get_user_config" in url or "get_profile" in url:
        return

    if "application/json" in content_type and URL_FILTER in url:
        try:
            data = response.json()
            captured_json.append({"url": url, "status": response.status, "data": data})
            extract_and_send_posts(data)
        except Exception:
            pass


def run_infinite_scroll():
    first_time = not os.path.exists(INITIAL_FLAG_FILE)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.on("response", handle_response)

        print(f">>> Navigating to {TARGET_URL}...")
        page.goto(TARGET_URL, wait_until="domcontentloaded")

        if first_time:
            print(f">>> First time run. Access the public noVNC URL to log in. Waiting {FIRST_RUN_WAIT_TIME // 60} min...")
            for remaining in range(FIRST_RUN_WAIT_TIME, 0, -30):
                print(f"[Login Window] {remaining}s remaining...")
                time.sleep(30)
            with open(INITIAL_FLAG_FILE, "w") as f:
                f.write("initialized")

        print("--- Fetching Initial Feed ---")
        last_height = 0
        for i in range(1, MAX_INITIAL_SCROLLS + 1):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            page.wait_for_timeout(SCROLL_DELAY)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(captured_json, f, indent=4, ensure_ascii=False)

        print(">>> Monitoring for live posts...")
        while True:
            time.sleep(POLL_INTERVAL)
            try:
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                page.evaluate("window.scrollTo(0, 400);")
            except Exception as e:
                print(f"Polling error: {e}")


if __name__ == "__main__":
    run_infinite_scroll()
