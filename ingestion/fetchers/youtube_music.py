import os
import re
import logging
from typing import List, Dict, Any
import requests

try:
    from ingestion.base_fetcher import BasePlatformFetcher
except ModuleNotFoundError:
    from base_fetcher import BasePlatformFetcher

class YouTubeMusicFetcher(BasePlatformFetcher):
    """
    Fetcher for YouTube Music Top 50 Global Songs.
    Extracts live daily top tracks via Kworb Live YouTube Global Daily Chart feed.
    """
    def __init__(self, api_key: str = None):
        super().__init__(platform_name="youtube_music")
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")

    def fetch_top_50(self) -> List[Dict[str, Any]]:
        self.logger.info("Fetching YouTube Music Top 50 Global tracks...")

        # 1. Primary Strategy: Live YouTube Global Daily Chart Extractor
        chart_tracks = self._fetch_live_youtube_global_chart()
        if chart_tracks:
            self.logger.info(f"Successfully extracted {len(chart_tracks)} LIVE Top 50 YouTube songs!")
            return chart_tracks
        
        # 3. Fallback: Standardized Sandbox Mock Data
        self.logger.warning("Falling back to mock YouTube Music data.")
        return self._generate_fallback_data()

    def _fetch_live_youtube_global_chart(self) -> List[Dict[str, Any]]:
        """
        Extracts real-time daily Top 50 YouTube Global Songs with Video IDs & View Counts.
        """
        url = "https://kworb.net/youtube/"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []

            matches = re.findall(
                r'<tr><td>(\d+)</td>.*?<a href="video/([^"]+)\.html">([^<]+)</a>.*?<td>([\d,]+)</td>',
                response.text,
                re.DOTALL
            )
            
            tracks = []
            for rank_str, video_id, title_artist, views_str in matches[:50]:
                rank = int(rank_str)
                views = int(views_str.replace(",", "")) if views_str.replace(",", "").isdigit() else None
                
                # Clean up (Official Video) type tags
                title_artist = re.sub(r'\s*\(.*?\)', '', title_artist)
                title_artist = re.sub(r'\s*\[.*?\]', '', title_artist)
                
                if " - " in title_artist:
                    parts = title_artist.split(" - ", 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    artist = "Unknown Artist"
                    title = title_artist.strip()
                
                record = self.build_raw_record(
                    platform_track_id=video_id,
                    track_name=title,
                    artist_name=artist,
                    rank=rank,
                    popularity_or_streams=views,
                    album_name="Single",
                    release_date=None,
                    duration_ms=None,
                    raw_json={"source": "kworb_live_youtube_chart", "youtube_video_id": video_id, "daily_views": views}
                )
                tracks.append(record)
            return tracks
        except Exception as e:
            self.logger.debug(f"Live chart extraction failed: {e}")
            return []

    def _generate_fallback_data(self) -> List[Dict[str, Any]]:
        sample_songs = [
            ("vid_01", "Espresso", "Sabrina Carpenter", 1, 1500000),
            ("vid_02", "BIRDS OF A FEATHER", "Billie Eilish", 2, 1400000),
            ("vid_03", "Good Luck, Babe!", "Chappell Roan", 3, 1300000),
            ("vid_04", "Please Please Please", "Sabrina Carpenter", 4, 1200000),
            ("vid_05", "Not Like Us", "Kendrick Lamar", 5, 1100000)
        ]
        results = []
        for track_id, title, artist, rank, views in sample_songs:
            results.append(self.build_raw_record(
                platform_track_id=track_id,
                track_name=title,
                artist_name=artist,
                rank=rank,
                popularity_or_streams=views,
                album_name="Single",
                release_date=None,
                duration_ms=None,
                raw_json={"source": "youtube_fallback_mock"}
            ))
        return results
