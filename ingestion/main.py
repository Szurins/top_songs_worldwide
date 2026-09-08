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
from ingestion.fetchers.youtube_music import YouTubeMusicFetcher
from ingestion.bronze_writer import BronzeJsonWriter

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.info("Starting Spotify & YouTube Music Top 50 JSON Ingestion Pipeline...")

    # Determine Amazon S3 Bucket from environment
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    writer = BronzeJsonWriter(s3_bucket=s3_bucket)

    # Fetch Spotify data
    try:
        spotify_fetcher = SpotifyFetcher()
        spotify_records = spotify_fetcher.fetch_top_50()
        writer.write_to_bronze(spotify_records, platform="spotify")
    except Exception as e:
        logging.error(f"Failed to fetch Spotify data: {e}")

    # Fetch YouTube Music data
    try:
        youtube_fetcher = YouTubeMusicFetcher()
        youtube_records = youtube_fetcher.fetch_top_50()
        writer.write_to_bronze(youtube_records, platform="youtube_music")
    except Exception as e:
        logging.error(f"Failed to fetch YouTube Music data: {e}")

if __name__ == "__main__":
    main()
