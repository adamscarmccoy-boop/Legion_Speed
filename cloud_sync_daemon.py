import os
import time
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("CloudSyncDaemon")

# Paths to local data
LANCEDB_PATH = os.environ.get("LANCEDB_PATH", r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag")
PARQUET_PATH = os.environ.get("PARQUET_PATH", r"C:\WEB CASE STUDY\takeout_vectorized.parquet")

# Cloudflare API Credentials (To be filled in by user)
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "your_account_id")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "your_api_token")
VECTORIZE_INDEX_NAME = "legion-intel-index"
R2_BUCKET_NAME = "legion-audio-bucket"

def sync_lancedb_to_vectorize():
    """
    Reads the local LanceDB tables and syncs them to Cloudflare Vectorize.
    This ensures the Cloudflare Edge Worker has instant access to your vectors.
    """
    logger.info(f"Checking for updates in local LanceDB at {LANCEDB_PATH}...")
    try:
        import lancedb
        if not os.path.exists(LANCEDB_PATH):
            logger.warning("LanceDB path does not exist yet.")
            return

        db = lancedb.connect(LANCEDB_PATH)
        tables = db.table_names()
        logger.info(f"Found tables: {tables}")
        
        for table_name in tables:
            tbl = db.open_table(table_name)
            # In a real implementation, you would track a 'last_synced' timestamp
            # and only push new rows to Cloudflare Vectorize via their REST API.
            # Example API call:
            # POST https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/vectorize/indexes/{VECTORIZE_INDEX_NAME}/insert
            logger.info(f"Mock Sync: Pushing new rows from '{table_name}' to Cloudflare Vectorize...")
            
    except Exception as e:
        logger.error(f"Failed to sync LanceDB: {e}")

def sync_audio_to_r2():
    """
    Syncs newly mastered audio or stems to Cloudflare R2.
    """
    mastered_dir = r"C:\WEB CASE STUDY\mastered_audio"
    logger.info(f"Checking for new audio files in {mastered_dir}...")
    
    if not os.path.exists(mastered_dir):
        return

    # In a real implementation, you would use boto3 (S3 compatible API) to upload to R2
    # Example:
    # s3.upload_file(local_file, R2_BUCKET_NAME, s3_key)
    for filename in os.listdir(mastered_dir):
        if filename.endswith(".wav") or filename.endswith(".mp3"):
            logger.info(f"Mock Sync: Uploading {filename} to Cloudflare R2 bucket '{R2_BUCKET_NAME}'...")

def run_sync_loop(interval_seconds=300):
    """
    Runs the daemon loop, syncing data every interval_seconds.
    """
    logger.info("Starting Dual System Cloud Sync Daemon...")
    while True:
        try:
            sync_lancedb_to_vectorize()
            sync_audio_to_r2()
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
            
        logger.info(f"Sleeping for {interval_seconds} seconds before next sync cycle.")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Run sync every 5 minutes (300 seconds)
    run_sync_loop(300)
