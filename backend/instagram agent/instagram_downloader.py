import argparse
import csv
import os
import sys
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import yt_dlp
except ImportError:
    print("Installing yt-dlp...")
    os.system("pip install yt-dlp")
    import yt_dlp

DOWNLOAD_FOLDER = Path(__file__).parent / "download"
CSV_FILE = Path(__file__).parent / "links.csv"
MAX_RETRIES = 3
MAX_WORKERS = 3
csv_lock = threading.Lock()
active_downloads = []
active_lock = threading.Lock()
download_counter = [0]

def setup():
    DOWNLOAD_FOLDER.mkdir(exist_ok=True)
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['link', 'status', 'filepath', 'timestamp'])

def get_existing_links():
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row['link'] for row in reader}

def get_pending_links():
    pending = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] in ('pending', 'failed'):
                pending.append(row['link'])
    return pending

def get_all_video_numbers(start_num, count):
    return list(range(start_num, start_num + count))

def update_csv(link, status, filepath=""):
    with csv_lock:
        rows = []
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        found = False
        for row in rows:
            if row['link'] == link:
                row['status'] = status
                row['filepath'] = filepath
                row['timestamp'] = timestamp
                found = True
                break
        
        if not found:
            rows.append({'link': link, 'status': status, 'filepath': filepath, 'timestamp': timestamp})
        
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['link', 'status', 'filepath', 'timestamp'])
            writer.writeheader()
            writer.writerows(rows)

def download_video(url, video_num, index, total):
    with active_lock:
        task_id = len(active_downloads) + 1
        active_downloads.append(task_id)
    
    update_csv(url, "downloading")
    
    output_template = str(DOWNLOAD_FOLDER / f"video_{video_num}")
    
    ydl_opts = {
        'outtmpl': output_template + '.%(ext)s',
        'format': 'best[ext=mp4]/bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'write_description': True,
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            if filename and os.path.exists(filename):
                with active_lock:
                    active_downloads.remove(task_id)
                rel_path = f"download/{os.path.basename(filename)}"
                update_csv(url, "done", rel_path)
                print(f"       + caption saved to .description file")
                return (True, video_num, url)
            else:
                raise Exception("File not found after download")
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2)
    
    with active_lock:
        active_downloads.remove(task_id)
    update_csv(url, "failed")
    return (False, video_num, url)

def print_progress(completed, total):
    bar_length = 20
    filled = int(bar_length * completed / total) if total > 0 else 0
    bar = "=" * filled + "-" * (bar_length - filled)
    return f"[{bar}] {completed}/{total}"

def get_input_links():
    print("\n" + "="*50)
    print("Enter Instagram links (one per line)")
    print("Press Enter twice to start downloading")
    print("="*50 + "\n")
    
    links = []
    while True:
        try:
            line = input().strip()
            if not line:
                if links:
                    break
                else:
                    print("Please enter at least one link")
                    continue
            links.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            sys.exit(0)
    
    return links

def main():
    parser = argparse.ArgumentParser(description='Instagram Video Downloader')
    parser.add_argument('--from-csv', action='store_true', help='Download pending/failed links from CSV')
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("  INSTAGRAM VIDEO DOWNLOADER")
    print("  (Parallel Downloads Enabled)")
    print("="*50)
    
    setup()
    
    if args.from_csv:
        links = get_pending_links()
        if not links:
            print("\nNo pending or failed links to download.")
            return
        print(f"\n[FROM CSV] Found {len(links)} pending/failed link(s)")
        new_links = links
        skipped = []
    else:
        existing_links = get_existing_links()
        links = get_input_links()
        
        new_links = []
        skipped = []
        for link in links:
            if link in existing_links:
                skipped.append(link)
            else:
                new_links.append(link)
        
        if not new_links:
            print("\nNo new links to download.")
            if skipped:
                print(f"({len(skipped)} links already downloaded, skipped)")
            return
    
    existing = list(DOWNLOAD_FOLDER.glob("video_*"))
    start_num = 1
    if existing:
        numbers = []
        for f in existing:
            name = f.stem
            if name.startswith("video_"):
                try:
                    numbers.append(int(name.split("_")[1]))
                except (ValueError, IndexError):
                    pass
        if numbers:
            start_num = max(numbers) + 1
    
    video_nums = get_all_video_numbers(start_num, len(new_links))
    
    print(f"\n{'='*50}")
    print(f"Starting parallel download of {len(new_links)} video(s)")
    print(f"Max concurrent downloads: {MAX_WORKERS}")
    print("="*50 + "\n")
    
    success_count = 0
    fail_count = 0
    completed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for i, link in enumerate(new_links):
            future = executor.submit(download_video, link, video_nums[i], i + 1, len(new_links))
            futures[future] = link
        
        for future in as_completed(futures):
            completed += 1
            success, video_num, url = future.result()
            
            if success:
                success_count += 1
                print(f"[{print_progress(completed, len(new_links))}] Done: video_{video_num}.mp4")
            else:
                fail_count += 1
                print(f"[{print_progress(completed, len(new_links))}] Failed: {url}")
    
    print(f"\n{'='*50}")
    print("  DOWNLOAD COMPLETE")
    print("="*50)
    print(f"  Successful: {success_count}")
    print(f"  Failed:     {fail_count}")
    print(f"  Location:   {DOWNLOAD_FOLDER}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
