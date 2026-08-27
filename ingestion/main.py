import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 1. Add project root directory to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 2. Automatically load environment variables from .env file
load_dotenv(dotenv_path=project_root / ".env")

from ingestion.fetchers.spotify import SpotifyFetcher
from ingestion.bronze_writer import BronzeJsonWriter

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.info("Starting Spotify Top 50 JSON Ingestion Pipeline...")

    # Fetch Spotify data
    fetcher = SpotifyFetcher()
    records = fetcher.fetch_top_50()

    # Determine Amazon S3 Bucket from environment
    s3_bucket = os.getenv("S3_BUCKET_NAME")

    # Upload directly to Amazon S3 Bucket (or local storage) in JSON format
    writer = BronzeJsonWriter(s3_bucket=s3_bucket)
    writer.write_to_bronze(records)

if __name__ == "__main__":
    main()
