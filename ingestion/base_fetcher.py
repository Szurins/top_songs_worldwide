import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class BasePlatformFetcher(ABC):
    """
    Abstract Base Class for Platform Fetchers with built-in retry logic,
    rate-limit handling, and standardized schema formatting.
    """
    def __init__(self, platform_name: str, max_retries: int = 5, backoff_factor: float = 1.0, dry_run: bool = False):
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"Fetcher.{platform_name}")
        self.dry_run = dry_run
        self.session = self._create_retry_session(max_retries, backoff_factor)

    def _create_retry_session(self, retries: int, backoff_factor: float) -> requests.Session:
        """
        Configures requests.Session with exponential backoff for HTTP 429 (Rate Limit),
        500, 502, 503, 504 status codes.
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _execute_request(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes HTTP request with explicit 429 Retry-After header inspection.
        """
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            
            # Specific 429 handling if Retry-After is supplied by API
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                self.logger.warning(f"Rate limit hit (429). Sleeping for {retry_after} seconds...")
                time.sleep(retry_after)
                response = self.session.get(url, headers=headers, params=params, timeout=15)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP Request failed for {url}: {e}")
            raise

    @abstractmethod
    def fetch_top_50(self) -> List[Dict[str, Any]]:
        """
        Must be implemented by platform subclass to fetch Top 50 tracks.
        """
        pass

    def build_raw_record(
        self,
        platform_track_id: str,
        track_name: str,
        artist_name: str,
        rank: int,
        popularity_or_streams: Optional[int] = None,
        album_name: Optional[str] = None,
        release_date: Optional[str] = None,
        duration_ms: Optional[int] = None,
        raw_json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Standardizes raw data payload before PySpark Delta Lake ingestion.
        """
        return {
            "platform": self.platform_name,
            "platform_track_id": str(platform_track_id),
            "track_name": track_name,
            "artist_name": artist_name,
            "rank": rank,
            "popularity_or_streams": popularity_or_streams,
            "album_name": album_name,
            "release_date": release_date,
            "duration_ms": duration_ms,
            "raw_payload": str(raw_json) if raw_json else "{}"
        }
