import os
import time
import requests
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")
FLAG_FILE = "session_initialized.flag"

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL or "YOUR_DISCORD" in DISCORD_WEBHOOK_URL:
        print("[ERROR] Discord Webhook URL is missing or unconfigured!", flush=True)
        return
    
    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
    if response.status_code in [200, 204]:
        print("[SUCCESS] Posted message to Discord!", flush=True)
    else:
        print(f"[ERROR] Discord Webhook failed with status {response.status_code}: {response.text}", flush=True)

def run_scraper():
    with sync_playwright() as p:
        print("[INFO] Launching Chromium browser context...", flush=True)
        browser = p.chromium.launch_persistent_context(
            user_data_dir="/tmp/playwright_user_data",
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page()
        
        target_url = "https://www.band.us/band/67130116/post"  # Replace with your specific Band URL
        print(f"[INFO] Navigating to {target_url}...", flush=True)
        page.goto(target_url, wait_until="networkidle")
        
        # Setup window if flag does not exist
        if not os.path.exists(FLAG_FILE):
            print("[INFO] Waiting 10 minutes for manual login via VNC...", flush=True)
            time.sleep(600)
            with open(FLAG_FILE, "w") as f:
                f.write("initialized")
            print("[INFO] 10-minute setup window finished.", flush=True)

        seen_posts = set()

        while True:
            try:
                print("[INFO] Scanning for post elements on screen...", flush=True)
                
                # Check for Band post containers (Update selector if Band modified their classes)
                posts = page.query_selector_all("div[class*='post'], article, ._postWrapper")
                print(f"[DEBUG] Found {len(posts)} post elements on page.", flush=True)

                for post in posts:
                    try:
                        text = post.inner_text().strip()
                        if text and text not in seen_posts:
                            seen_posts.add(text)
                            print(f"[NEW POST DETECTED]: {text[:50]}...", flush=True)
                            send_to_discord(f"**New Band Post:**\n{text[:1500]}")
                    except Exception as e:
                        print(f"[WARNING] Could not read post text: {e}", flush=True)

                # Scroll down
                print("[INFO] Scrolling down...", flush=True)
                page.evaluate("window.scrollBy(0, 1000);")
                time.sleep(5)

            except Exception as main_err:
                print(f"[ERROR] Loop error: {main_err}", flush=True)
                time.sleep(5)

if __name__ == "__main__":
    run_scraper()
