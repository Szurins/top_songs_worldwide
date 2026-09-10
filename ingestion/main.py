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
from ingestion.fetchers.apple_music import AppleMusicFetcher
from ingestion.bronze_writer import BronzeJsonWriter

import argparse

def main():
    parser = argparse.ArgumentParser(description="Top Songs Worldwide Ingestion Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Skip live fetching and return mock data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.info(f"Starting Spotify, YouTube Music & Apple Music Top 50 JSON Ingestion Pipeline... (Dry run: {args.dry_run})")

    # Determine Amazon S3 Bucket from environment
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    writer = BronzeJsonWriter(s3_bucket=s3_bucket)

    # Fetch Spotify data
    try:
        spotify_fetcher = SpotifyFetcher(dry_run=args.dry_run)
        spotify_records = spotify_fetcher.fetch_top_50()
        writer.write_to_bronze(spotify_records, platform="spotify")
    except Exception as e:
        logging.error(f"Failed to fetch Spotify data: {e}")

    # Fetch YouTube Music data
    try:
        youtube_fetcher = YouTubeMusicFetcher(dry_run=args.dry_run)
        youtube_records = youtube_fetcher.fetch_top_50()
        writer.write_to_bronze(youtube_records, platform="youtube_music")
    except Exception as e:
        logging.error(f"Failed to fetch YouTube Music data: {e}")

    # Fetch Apple Music data
    try:
        apple_fetcher = AppleMusicFetcher(dry_run=args.dry_run)
        apple_records = apple_fetcher.fetch_top_50()
        writer.write_to_bronze(apple_records, platform="apple_music")
    except Exception as e:
        logging.error(f"Failed to fetch Apple Music data: {e}")

if __name__ == "__main__":
    main()
