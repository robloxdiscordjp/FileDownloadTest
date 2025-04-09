import os
import time
import requests
import logging
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_size(bytes_num):
    """バイト数を人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} TB"

def format_speed(bytes_per_sec):
    """ダウンロード速度を人間が読みやすい形式に変換"""
    return format_size(bytes_per_sec) + "/s"

def download_speed_test():
    """ダウンロード速度テストを実行"""
    # 環境変数の読み込み
    load_dotenv()
    download_url = os.getenv("DOWNLOAD_URL")
    
    if not download_url:
        logger.error("Error: DOWNLOAD_URL not specified in .env file")
        return
    
    logger.info(f"Starting download test from: {download_url}")
    
    # 測定値の初期化
    start_time = time.time()
    first_byte_time = None
    total_bytes = 0
    last_report_time = start_time
    last_report_bytes = 0
    
    try:
        # リクエスト開始
        session = requests.Session()
        
        # DNS解決と接続時間の測定
        dns_start = time.time()
        response = session.get(download_url, stream=True, timeout=30)
        connection_time = time.time() - dns_start
        
        # レスポンスコード確認
        if response.status_code != 200:
            logger.error(f"Error: HTTP Status {response.status_code}")
            return
            
        # ヘッダー情報
        content_length = response.headers.get('Content-Length')
        if content_length:
            logger.info(f"Content size: {format_size(int(content_length))}")
        
        # チャンク単位でダウンロード（メモリに保持しない）
        for chunk in response.iter_content(chunk_size=8192):
            if first_byte_time is None:
                first_byte_time = time.time()
                ttfb = first_byte_time - start_time
                logger.info(f"Time to first byte (latency): {ttfb:.4f} seconds")
            
            if chunk:  # keep-aliveチャンクをフィルタ
                chunk_size = len(chunk)
                total_bytes += chunk_size
                
                # 5秒ごとに進捗報告
                current_time = time.time()
                if current_time - last_report_time > 5:
                    # 現在の速度計算
                    interval = current_time - last_report_time
                    interval_bytes = total_bytes - last_report_bytes
                    current_speed = interval_bytes / interval
                    
                    logger.info(f"Downloaded: {format_size(total_bytes)}, "
                                f"Current speed: {format_speed(current_speed)}")
                    
                    last_report_time = current_time
                    last_report_bytes = total_bytes
        
        # 最終測定値の計算
        end_time = time.time()
        total_time = end_time - start_time
        download_time = end_time - first_byte_time
        
        # レイテンシー計算
        ttfb = first_byte_time - start_time if first_byte_time else None
        
        # 結果表示
        logger.info("\n===== Download Test Results =====")
        logger.info(f"URL: {download_url}")
        logger.info(f"Total time: {total_time:.4f} seconds")
        logger.info(f"Connection time: {connection_time:.4f} seconds")
        if ttfb:
            logger.info(f"Latency (TTFB): {ttfb:.4f} seconds")
        logger.info(f"Download time: {download_time:.4f} seconds")
        logger.info(f"Downloaded size: {format_size(total_bytes)}")
        logger.info(f"Average download speed: {format_speed(total_bytes / download_time)}")
        logger.info(f"Throughput: {format_speed(total_bytes / total_time)}")
        logger.info("================================")
        
    except Exception as e:
        logger.error(f"Error during download test: {e}")

if __name__ == "__main__":
    download_speed_test()
