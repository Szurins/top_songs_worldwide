import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

class BronzeJsonWriter:
    """
    Writes raw Top 50 records directly to an Amazon S3 Bucket in JSON format.
    Fails immediately if S3 configuration, credentials, or permissions are invalid.
    No local fallback saving!
    """
    PLACEHOLDER_KEYS = {
        "your_aws_access_key_id_here",
        "your_aws_secret_access_key_here",
        "your_s3_bucket_name_here",
        "my-spotify-top-songs-bucket",
        "my-top-songs-data-bucket"
    }

    def __init__(self, s3_bucket: Optional[str] = None, s3_prefix: str = "raw/top_songs"):
        self.logger = logging.getLogger("BronzeWriter.S3")
        
        bucket_name = (s3_bucket or os.getenv("S3_BUCKET_NAME", "")).strip()
        aws_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()

        # Validate S3 bucket & AWS credentials strictly
        if not bucket_name or bucket_name in self.PLACEHOLDER_KEYS:
            raise ValueError(f"[ERROR] Invalid or missing S3_BUCKET_NAME in .env: '{bucket_name}'. Execution stopped.")

        if not aws_key or aws_key in self.PLACEHOLDER_KEYS:
            raise ValueError("[ERROR] AWS_ACCESS_KEY_ID is missing or set to placeholder in .env. Execution stopped.")

        if not aws_secret or aws_secret in self.PLACEHOLDER_KEYS:
            raise ValueError("[ERROR] AWS_SECRET_ACCESS_KEY is missing or set to placeholder in .env. Execution stopped.")

        self.s3_bucket = bucket_name.replace("s3://", "").strip("/")
        self.s3_prefix = s3_prefix.strip("/")
        
        aws_region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-north-1")).strip()
        aws_token = os.getenv("AWS_SESSION_TOKEN", "").strip()
        
        session_kwargs = {
            "aws_access_key_id": aws_key,
            "aws_secret_access_key": aws_secret,
            "region_name": aws_region
        }
        if aws_token:
            session_kwargs["aws_session_token"] = aws_token

        self.s3_client = boto3.client("s3", **session_kwargs)

    def write_to_bronze(self, records: List[Dict[str, Any]], platform: str):
        if not records:
            raise ValueError("[ERROR] No track records available to upload to S3. Execution stopped.")

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")

        payload = {
            "ingested_at": now.isoformat(),
            "ingested_date": date_str,
            "platform": platform,
            "record_count": len(records),
            "tracks": records
        }

        filename = f"{platform}_top_songs_{date_str}_{timestamp_str}.json"
        json_data = json.dumps(payload, indent=2, ensure_ascii=False)

        dynamic_prefix = f"{self.s3_prefix}/{platform}_top_songs" if self.s3_prefix == "raw/top_songs" else self.s3_prefix
        s3_key = f"{dynamic_prefix}/{date_str}/{filename}"
        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
        
        self.logger.info(f"Uploading {len(records)} {platform} tracks to Amazon S3: {s3_uri}")
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json_data.encode("utf-8"),
                ContentType="application/json"
            )
            self.logger.info(f"[SUCCESS] {platform} JSON uploaded to Amazon S3: {s3_uri}")
        except ClientError as e:
            self.logger.error(f"[FAILURE] S3 Upload failed ({e}). Execution stopped.")
            raise RuntimeError(f"S3 Upload failed: {e}") from e
