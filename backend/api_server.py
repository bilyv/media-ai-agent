import csv
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
from datetime import datetime

CSV_FILE = Path(__file__).parent / "instagram agent" / "links.csv"
DOWNLOADER_PATH = Path(__file__).parent / "instagram agent" / "instagram_downloader.py"
GRABBER_PATH = Path(__file__).parent / "link grabber agent" / "link-clipboard.py"

class APIHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/api/links':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            links = []
            if CSV_FILE.exists():
                with open(CSV_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    links = list(reader)
            
            self.wfile.write(json.dumps(links).encode())
            
        elif self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            stats = {'pending': 0, 'downloading': 0, 'done': 0, 'failed': 0}
            if CSV_FILE.exists():
                with open(CSV_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        status = row.get('status', 'pending')
                        if status in stats:
                            stats[status] += 1
            
            self.wfile.write(json.dumps(stats).encode())
        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/download':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            try:
                result = subprocess.run(
                    [sys.executable, str(DOWNLOADER_PATH), "--from-csv"],
                    capture_output=True,
                    text=True
                )
                response = {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr}
            except Exception as e:
                response = {'success': False, 'error': str(e)}
            
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/grab':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            try:
                result = subprocess.run(
                    [sys.executable, str(GRABBER_PATH)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                response = {'success': True, 'output': result.stdout}
            except subprocess.TimeoutExpired:
                response = {'success': True, 'output': 'Grabber started (runs in background)'}
            except Exception as e:
                response = {'success': False, 'error': str(e)}
            
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/add-link':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                link = data.get('link', '').strip()
                
                if not link:
                    response = {'success': False, 'error': 'No link provided'}
                else:
                    existing_links = set()
                    if CSV_FILE.exists():
                        with open(CSV_FILE, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            existing_links = {row['link'] for row in reader}
                    
                    if link in existing_links:
                        response = {'success': False, 'error': 'Link already exists'}
                    else:
                        file_exists = CSV_FILE.exists()
                        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(['link', 'status', 'filepath', 'timestamp'])
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            writer.writerow([link, 'pending', '', timestamp])
                        response = {'success': True, 'message': 'Link added successfully'}
            except Exception as e:
                response = {'success': False, 'error': str(e)}
            
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/download-single':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                link = data.get('link', '').strip()
                
                if not link:
                    response = {'success': False, 'error': 'No link provided'}
                else:
                    result = subprocess.run(
                        [sys.executable, str(DOWNLOADER_PATH), "--from-csv"],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    response = {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr}
            except Exception as e:
                response = {'success': False, 'error': str(e)}
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_server(port=5000):
    server = HTTPServer(('localhost', port), APIHandler)
    print(f"API Server running on http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
