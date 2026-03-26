import requests
import time
import os
import random
import csv
from datetime import datetime

# main.pyから引用したUser-Agent
user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1'
]

TIMEOUT = (1.5, 1.0) 

def get_headers():
    return {'User-Agent': random.choice(user_agents)}

def test_endpoint(base_url, path):
    start_time = time.time()
    try:
        url = f"{base_url.rstrip('/')}/api/v1{path}"
        res = requests.get(url, headers=get_headers(), timeout=TIMEOUT)
        duration = time.time() - start_time
        
        if res.status_code == 200:
            # プレイリスト等の中身が空でないか簡易チェック
            info = res.text[:100].replace('\n', ' ').replace(',', ' ')
            return "OK", duration, info
        else:
            return f"Error({res.status_code})", duration, "Invalid Status"
    except Exception as e:
        return "Failed", time.time() - start_time, str(e)[:50]

def monitor():
    if not os.path.exists('instances.txt'):
        return

    with open('instances.txt', 'r') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    os.makedirs('logs', exist_ok=True)
    
    # テスト項目（Playlistを追加）
    test_paths = {
        "Video": "/videos/jNQXAC9IVRw",
        "Search": "/search?q=test",
        "Channel": "/channels/UC1cfCbochfBCAuEES8asvJA",
        "Comments": "/comments/jNQXAC9IVRw",
        "Playlist": "/playlists/PLe9uW8S9YfE_9ZlToxI-X_38L3r4Fh_pX" # 公開プレイリストの例
    }

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    for domain in domains:
        file_name = domain.replace("https://", "").replace("http://", "").replace("/", "_")
        csv_path = f"logs/{file_name}.csv"
        
        file_exists = os.path.exists(csv_path)
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Category", "Status", "ResponseTime", "RawData"])

            for cat, path in test_paths.items():
                status, duration, info = test_endpoint(domain, path)
                writer.writerow([now_str, cat, status, round(duration, 3), info])

if __name__ == "__main__":
    monitor()
