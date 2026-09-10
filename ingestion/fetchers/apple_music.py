import os
import logging
from typing import List, Dict, Any
import requests

try:
    from ingestion.base_fetcher import BasePlatformFetcher
except ModuleNotFoundError:
    from base_fetcher import BasePlatformFetcher

class AppleMusicFetcher(BasePlatformFetcher):
    """
    Fetcher for Apple Music Top 50 Songs.
    Extracts live daily top tracks via Apple Music RSS Feed API.
    """
    def __init__(self, dry_run: bool = False):
        super().__init__(platform_name="apple_music", dry_run=dry_run)

    def fetch_top_50(self) -> List[Dict[str, Any]]:
        self.logger.info("Fetching Apple Music Top 50 tracks...")

        if self.dry_run:
            self.logger.info("[DRY RUN] Skipping live fetch, returning mock data.")
            return self._generate_fallback_data()

        # 1. Primary Strategy: Apple Music RSS Feed (US Most Played)
        chart_tracks = self._fetch_live_apple_music_rss()
        if chart_tracks:
            self.logger.info(f"Successfully extracted {len(chart_tracks)} LIVE Top 50 Apple Music songs!")
            return chart_tracks
        
        # 2. Fallback: Standardized Sandbox Mock Data
        self.logger.warning("Falling back to mock Apple Music data.")
        return self._generate_fallback_data()

    def _fetch_live_apple_music_rss(self) -> List[Dict[str, Any]]:
        """
        Extracts daily Top 50 Apple Music Songs from official RSS JSON feed.
        """
        # Using US Most Played as proxy for Global, since Apple Music RSS generator often targets storefronts
        url = "https://rss.applemarketingtools.com/api/v2/us/music/most-played/50/songs.json"
        
        try:
            data = self._execute_request(url)
            results = data.get("feed", {}).get("results", [])
            
            tracks = []
            for idx, item in enumerate(results[:50], start=1):
                track_id = item.get("id")
                title = item.get("name", "Unknown Title")
                artist = item.get("artistName", "Unknown Artist")
                release_date = item.get("releaseDate")
                album = item.get("collectionName", "Single") # RSS sometimes doesn't have collectionName directly at root for songs, but let's check or just default to None
                
                record = self.build_raw_record(
                    platform_track_id=track_id,
                    track_name=title,
                    artist_name=artist,
                    rank=idx,
                    popularity_or_streams=None, # Apple Music RSS does not provide play counts
                    album_name=album,
                    release_date=release_date,
                    duration_ms=None,
                    raw_json=item
                )
                tracks.append(record)
            return tracks
        except Exception as e:
            self.logger.debug(f"Live RSS extraction failed: {e}")
            return []

    def _generate_fallback_data(self) -> List[Dict[str, Any]]:
        sample_songs = [
            ("am_01", "Espresso", "Sabrina Carpenter", 1, None, "Short n' Sweet", "2024-04-11", 175466),
            ("am_02", "BIRDS OF A FEATHER", "Billie Eilish", 2, None, "HIT ME HARD AND SOFT", "2024-05-17", 199800),
            ("am_03", "Good Luck, Babe!", "Chappell Roan", 3, None, "Good Luck, Babe!", "2024-04-05", 218423),
            ("am_04", "Please Please Please", "Sabrina Carpenter", 4, None, "Short n' Sweet", "2024-06-06", 186365),
            ("am_05", "Not Like Us", "Kendrick Lamar", 5, None, "Not Like Us", "2024-05-04", 274192)
        ]
        results = []
        for track_id, title, artist, rank, streams, album, r_date, dur in sample_songs:
            results.append(self.build_raw_record(
                platform_track_id=track_id,
                track_name=title,
                artist_name=artist,
                rank=rank,
                popularity_or_streams=streams,
                album_name=album,
                release_date=r_date,
                duration_ms=dur,
                raw_json={"source": "apple_music_fallback_mock"}
            ))
        return results
