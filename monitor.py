import requests
import time
import csv
import os
from datetime import datetime, timedelta

INSTANCE_FILE = "instances.txt"
LOG_DIR = "logs"
RETENTION_DAYS = 30  # 保存期間（日）

# 検証するエンドポイント（動画IDは共通のものを利用）
VIDEO_ID = "jNQXAC9IVRw"
TEST_PATHS = {
    "VideoInfo": f"/api/v1/videos/{VIDEO_ID}",
    "Stream": f"/api/v1/videos/{VIDEO_ID}",
    "Comments": f"/api/v1/comments/{VIDEO_ID}",  # コメント取得を追加
    "Search": "/api/v1/search?q=open_source",
    "Playlist": "/api/v1/playlists/PLBCF2DAC6FFB574DE"
}

def run_monitor():
    if not os.path.exists(INSTANCE_FILE):
        print("Error: instances.txt がありません")
        return

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    with open(INSTANCE_FILE, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    now = datetime.now()
    headers = {'User-Agent': 'Invidious-Monitor/1.0'}

    for domain in domains:
        # ドメイン名からファイル名を作成 (例: inv.tux.im.csv)
        file_safe_name = domain.replace("https://", "").replace("http://", "").replace("/", "_")
        log_file = os.path.join(LOG_DIR, f"{file_safe_name}.csv")
        
        # 新規ファイルならヘッダー作成
        file_exists = os.path.isfile(log_file)
        
        current_results = []
        for label, path in TEST_PATHS.items():
            full_url = domain.rstrip('/') + path
            start_time = time.time()
            try:
                res = requests.get(full_url, headers=headers, timeout=10)
                duration = round(time.time() - start_time, 3)
                status = "OK" if res.status_code == 200 else f"HTTP_{res.status_code}"
            except Exception:
                duration = round(time.time() - start_time, 3)
                status = "Timeout/Error"
            
            current_results.append([now.strftime("%Y-%m-%d %H:%M"), label, status, duration])

        # --- データの読み込みと30日間のフィルタリング ---
        all_logs = []
        if file_exists:
            with open(log_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                threshold = now - timedelta(days=RETENTION_DAYS)
                for row in reader:
                    # 日時をパースして保存期間内かチェック
                    log_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
                    if log_date > threshold:
                        all_logs.append(row)

        # --- 新しい結果を追加して保存 ---
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["日時", "検証項目", "ステータス", "応答速度(s)"])
            writer.writerows(all_logs)      # 過去30日分のデータ
            writer.writerows(current_results) # 今回の結果
            
        print(f"Finished: {domain} -> {log_file}")

if __name__ == "__main__":
    run_monitor()
