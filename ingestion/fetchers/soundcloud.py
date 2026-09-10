import os
from typing import List, Dict, Any

try:
    from ingestion.base_fetcher import BasePlatformFetcher
except ModuleNotFoundError:
    from base_fetcher import BasePlatformFetcher

class SoundcloudFetcher(BasePlatformFetcher):
    """
    Fetcher for SoundCloud Top 50 Global Songs.
    Extracts top tracks using the SoundCloud API (if client_id is provided) or mock data.
    """
    def __init__(self, client_id: str = None, dry_run: bool = False):
        super().__init__(platform_name="soundcloud", dry_run=dry_run)
        self.client_id = client_id or os.getenv("SOUNDCLOUD_CLIENT_ID")

    def fetch_top_50(self) -> List[Dict[str, Any]]:
        self.logger.info("Fetching SoundCloud Top 50 Global tracks...")

        if self.dry_run:
            self.logger.info("[DRY RUN] Skipping live fetch, returning mock data.")
            return self._generate_fallback_data()

        # 1. Primary Strategy: SoundCloud API v2
        if self.client_id and self.client_id != "your_soundcloud_client_id_here":
            chart_tracks = self._fetch_live_soundcloud_api()
            if chart_tracks:
                self.logger.info(f"Successfully extracted {len(chart_tracks)} LIVE Top 50 SoundCloud songs!")
                return chart_tracks
        else:
            self.logger.warning("No SOUNDCLOUD_CLIENT_ID provided. Skipping live API fetch.")
        
        # 2. Fallback: Standardized Sandbox Mock Data
        self.logger.warning("Falling back to mock SoundCloud data.")
        return self._generate_fallback_data()

    def _fetch_live_soundcloud_api(self) -> List[Dict[str, Any]]:
        """
        Extracts daily Top 50 SoundCloud Songs from API v2.
        """
        url = "https://api-v2.soundcloud.com/charts"
        params = {
            "kind": "top",
            "genre": "soundcloud:genres:all-music",
            "limit": 50,
            "client_id": self.client_id
        }
        
        try:
            data = self._execute_request(url, params=params)
            collection = data.get("collection", [])
            
            tracks = []
            for idx, item in enumerate(collection[:50], start=1):
                track = item.get("track", {})
                if not track: continue

                track_id = track.get("id")
                title = track.get("title", "Unknown Title")
                artist = track.get("user", {}).get("username", "Unknown Artist")
                release_date = track.get("created_at")
                playback_count = track.get("playback_count")
                duration = track.get("duration")
                
                record = self.build_raw_record(
                    platform_track_id=track_id,
                    track_name=title,
                    artist_name=artist,
                    rank=idx,
                    popularity_or_streams=playback_count,
                    album_name="Single",
                    release_date=release_date,
                    duration_ms=duration,
                    raw_json=item
                )
                tracks.append(record)
            return tracks
        except Exception as e:
            self.logger.debug(f"Live API extraction failed: {e}")
            return []

    def _generate_fallback_data(self) -> List[Dict[str, Any]]:
        sample_songs = [
            ("sc_01", "Espresso (Remix)", "DJ Sabrina", 1, 5500000, "Remixes Vol 1", "2024-04-15", 200000),
            ("sc_02", "BIRDS OF A FEATHER (Lo-fi)", "Chill Billie", 2, 4200000, "Lo-fi Beats", "2024-05-20", 180000),
            ("sc_03", "Good Luck, Babe! (Club Edit)", "Chappell Roan", 3, 3100000, "Club Edits", "2024-04-10", 250000),
            ("sc_04", "Please Please Please (Acoustic)", "Sabrina C.", 4, 2800000, "Acoustic Sessions", "2024-06-10", 195000),
            ("sc_05", "Not Like Us (Instrumental)", "Kendrick Lamar", 5, 2500000, "Beats", "2024-05-06", 270000)
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
                raw_json={"source": "soundcloud_fallback_mock"}
            ))
        return results
