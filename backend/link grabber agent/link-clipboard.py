import argparse
import csv
import os
import subprocess
import sys
import time
import re
from datetime import datetime
from pathlib import Path

def install_pyperclip():
    try:
        import pyperclip
        return pyperclip
    except ImportError:
        print("Installing pyperclip...")
        os.system("pip install pyperclip")
        import pyperclip
        return pyperclip

SCRIPT_DIR = Path(__file__).parent
LINKS_CSV = SCRIPT_DIR.parent / "instagram agent" / "links.csv"

INSTAGRAM_PATTERN = re.compile(
    r'(https?://)?(www\.)?instagram\.com/(p|reels?|tv)/[A-Za-z0-9_-]+/?',
    re.IGNORECASE
)

def extract_url(text):
    match = INSTAGRAM_PATTERN.search(text)
    if match:
        url = match.group(0)
        if not url.startswith('http'):
            url = 'https://' + url
        return url.rstrip('/')
    return None

def load_existing_links():
    if not LINKS_CSV.exists():
        return set()
    with open(LINKS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row['link'] for row in reader}

def save_link_to_csv(link):
    file_exists = LINKS_CSV.exists()
    
    with open(LINKS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['link', 'status', 'filepath', 'timestamp'])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([link, 'pending', '', timestamp])
    
    return True

def main():
    print("\n" + "=" * 60)
    print("  INSTAGRAM CLIPBOARD LINK GRABBER")
    print("=" * 60)
    print()
    print("  HOW TO USE:")
    print("  1. Copy any Instagram URL from anywhere")
    print("  2. Program auto-detects and saves it")
    print("  3. Duplicate links are automatically skipped")
    print("  4. Press Ctrl+C to stop")
    print()
    print("=" * 60)
    
    pyperclip = install_pyperclip()
    
    existing_links = load_existing_links()
    saved_count = len(existing_links)
    new_count = 0
    last_clipboard = ""
    
    print(f"\n[STARTED] Monitoring clipboard...")
    print(f"[INFO] Loaded {saved_count} existing links from CSV")
    print(f"[INFO] Output: {LINKS_CSV}")
    print("-" * 60)
    
    try:
        while True:
            try:
                current_clipboard = pyperclip.paste()
                
                if current_clipboard and current_clipboard != last_clipboard:
                    last_clipboard = current_clipboard
                    url = extract_url(current_clipboard)
                    
                    if url:
                        print(f"\n[DETECTED] {url}")
                        
                        if url in existing_links:
                            print(f"[SKIPPED] Already exists in CSV")
                        else:
                            save_link_to_csv(url)
                            existing_links.add(url)
                            new_count += 1
                            saved_count += 1
                            print(f"[SAVED] New link saved! (Total: {saved_count})")
                    else:
                        # Only show detection for non-empty clipboard content
                        if len(current_clipboard.strip()) > 5:
                            print(f"[CHECKED] Not an Instagram URL")
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(1)
                
    except KeyboardInterrupt:
        pass
    
    print("\n" + "=" * 60)
    print("  MONITOR STOPPED")
    print("=" * 60)
    print(f"  Total links in CSV: {saved_count}")
    print(f"  New links saved: {new_count}")
    print(f"  Location: {LINKS_CSV}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Instagram Clipboard Link Grabber')
    parser.add_argument('--download', action='store_true', help='Download pending/failed links from CSV')
    args = parser.parse_args()
    
    if args.download:
        downloader_path = SCRIPT_DIR.parent / "instagram agent" / "instagram_downloader.py"
        print(f"[DOWNLOAD] Running downloader...")
        result = subprocess.run([sys.executable, str(downloader_path), "--from-csv"])
        sys.exit(result.returncode)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOPPED] Monitor closed")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
