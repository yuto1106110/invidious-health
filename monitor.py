import requests
import time
import os
import random
import csv
from datetime import datetime, timedelta

# main.pyから引用したUser-Agent
user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1'
]

# main.pyと同じ厳しい設定 (接続, 読み込み)
TIMEOUT = (1.5, 1.0) 
RETENTION_DAYS = 30 # 30日分保存

def get_headers():
    return {'User-Agent': random.choice(user_agents)}

def test_endpoint(base_url, path):
    """リトライ機能を搭載して成功率を向上させる"""
    full_url = f"{base_url.rstrip('/')}/api/v1{path}"
    
    # 最大2回試行（1回失敗してもリトライ）
    for attempt in range(2):
        start_time = time.time()
        try:
            res = requests.get(full_url, headers=get_headers(), timeout=TIMEOUT)
            duration = time.time() - start_time
            if res.status_code == 200:
                # 成功
                info = res.text[:100].replace('\n', ' ').replace(',', ' ')
                return "OK", duration, info
        except Exception:
            pass
        
        # 失敗した場合は0.5秒待って再試行
        if attempt == 0:
            time.sleep(0.5)
            
    return "Failed", time.time() - start_time, "Timeout or Error"

def monitor():
    if not os.path.exists('instances.txt'):
        return

    with open('instances.txt', 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    os.makedirs('logs', exist_ok=True)
    
    # 調査項目
    test_paths = {
        "Video": "/videos/jNQXAC9IVRw",
        "Search": "/search?q=test",
        "Channel": "/channels/UC1cfCbochfBCAuEES8asvJA",
        "Comments": "/comments/jNQXAC9IVRw",
        "Playlist": "/playlists/PLe9uW8S9YfE_9ZlToxI-X_38L3r4Fh_pX"
    }

    # 日本時間 (JST) を取得
    now_jst = datetime.utcnow() + timedelta(hours=9)
    now_str = now_jst.strftime('%Y-%m-%d %H:%M')
    threshold = now_jst - timedelta(days=RETENTION_DAYS)

    for domain in domains:
        print(f"Checking {domain}...")
        file_name = domain.replace("https://", "").replace("http://", "").replace("/", "_")
        csv_path = f"logs/{file_name}.csv"
        
        # 既存ログの読み込み（30日分ローテーション）
        old_rows = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    try:
                        log_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                        if log_date > threshold:
                            old_rows.append(row)
                    except: pass

        # 今回の結果を取得
        current_results = []
        for cat, path in test_paths.items():
            status, duration, info = test_endpoint(domain, path)
            current_results.append([now_str, cat, status, round(duration, 3), info])

        # 保存
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Category", "Status", "ResponseTime", "RawData"])
            writer.writerows(old_rows)
            writer.writerows(current_results)

if __name__ == "__main__":
    monitor()
