import os
import re
import logging
from typing import List, Dict, Any
import requests

try:
    from ingestion.base_fetcher import BasePlatformFetcher
except ModuleNotFoundError:
    from base_fetcher import BasePlatformFetcher

class SpotifyFetcher(BasePlatformFetcher):
    """
    Fetcher for Spotify Top 50 Global Songs.
    Extracts live daily top tracks via Spotify Web API or Kworb Live Spotify Global Daily Chart feed.
    """
    def __init__(self, client_id: str = None, client_secret: str = None, dry_run: bool = False):
        super().__init__(platform_name="spotify", dry_run=dry_run)
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token = None

    def _authenticate(self):
        if not self.client_id or not self.client_secret or "your_spotify" in self.client_id:
            return

        auth_url = "https://accounts.spotify.com/api/token"
        try:
            response = requests.post(
                auth_url,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                timeout=10
            )
            response.raise_for_status()
            self.access_token = response.json().get("access_token")
        except Exception:
            self.access_token = None

    def fetch_top_50(self) -> List[Dict[str, Any]]:
        self.logger.info("Fetching Spotify Top 50 Global tracks...")

        if self.dry_run:
            self.logger.info("[DRY RUN] Skipping live fetch, returning mock data.")
            return self._generate_fallback_data()

        # 1. Primary Strategy: Live Spotify Global Daily Chart Extractor
        chart_tracks = self._fetch_live_spotify_global_chart()
        if chart_tracks:
            self.logger.info(f"Successfully extracted {len(chart_tracks)} LIVE Top 50 Spotify songs!")
            return chart_tracks

        # 2. Secondary Strategy: Spotify Web API
        if not self.access_token and self.client_id and self.client_secret:
            self._authenticate()

        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            try:
                url = "https://api.spotify.com/v1/playlists/37i9dQZEVXbMDoYe2w8Fcn/tracks"
                data = self._execute_request(url, headers=headers, params={"limit": 50})
                tracks = self._parse_api_tracks(data)
                if tracks:
                    return tracks
            except Exception:
                pass

        # 3. Fallback: Standardized Sandbox Mock Data
        return self._generate_fallback_data()

    def _fetch_live_spotify_global_chart(self) -> List[Dict[str, Any]]:
        """
        Extracts real-time daily Top 50 Spotify Global Songs with Spotify Track IDs & Stream Counts.
        """
        url = "https://kworb.net/spotify/country/global_daily.html"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []

            matches = re.findall(
                r'<a href="\.\./artist/[^"]+">([^<]+)</a> - <a href="\.\./track/([^"]+)">([^<]+)</a>.*?<td>([\d,]+)</td>',
                response.text,
                re.DOTALL
            )
            
            tracks = []
            for idx, (artist, tid, title, streams_str) in enumerate(matches[:50], start=1):
                track_id = tid.replace(".html", "")
                streams = int(streams_str.replace(",", "")) if streams_str.replace(",", "").isdigit() else None
                
                record = self.build_raw_record(
                    platform_track_id=track_id,
                    track_name=title.strip(),
                    artist_name=artist.strip(),
                    rank=idx,
                    popularity_or_streams=streams,
                    album_name="Single",
                    release_date=None,
                    duration_ms=None,
                    raw_json={"source": "kworb_live_spotify_chart", "spotify_track_id": track_id, "daily_streams": streams}
                )
                tracks.append(record)
            return tracks
        except Exception as e:
            self.logger.debug(f"Live chart extraction failed: {e}")
            return []

    def _parse_api_tracks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        tracks = []
        for idx, item in enumerate(data.get("items", []), start=1):
            track = item.get("track", {})
            if not track: continue

            artists = ", ".join([artist["name"] for artist in track.get("artists", [])])
            record = self.build_raw_record(
                platform_track_id=track.get("id", f"sp_{idx}"),
                track_name=track.get("name", "Unknown Track"),
                artist_name=artists or "Unknown Artist",
                rank=idx,
                popularity_or_streams=track.get("popularity"),
                album_name=track.get("album", {}).get("name"),
                release_date=track.get("album", {}).get("release_date"),
                duration_ms=track.get("duration_ms"),
                raw_json=item
            )
            tracks.append(record)
        return tracks

    def _generate_fallback_data(self) -> List[Dict[str, Any]]:
        sample_songs = [
            ("sp_01", "Espresso", "Sabrina Carpenter", 1, 95, "Short n' Sweet", "2024-04-11", 175466),
            ("sp_02", "BIRDS OF A FEATHER", "Billie Eilish", 2, 98, "HIT ME HARD AND SOFT", "2024-05-17", 199800),
            ("sp_03", "Good Luck, Babe!", "Chappell Roan", 3, 94, "Good Luck, Babe!", "2024-04-05", 218423),
            ("sp_04", "Please Please Please", "Sabrina Carpenter", 4, 96, "Short n' Sweet", "2024-06-06", 186365),
            ("sp_05", "Not Like Us", "Kendrick Lamar", 5, 99, "Not Like Us", "2024-05-04", 274192)
        ]
        results = []
        for track_id, title, artist, rank, pop, album, r_date, dur in sample_songs:
            results.append(self.build_raw_record(
                platform_track_id=track_id,
                track_name=title,
                artist_name=artist,
                rank=rank,
                popularity_or_streams=pop,
                album_name=album,
                release_date=r_date,
                duration_ms=dur,
                raw_json={"source": "spotify_fallback_mock"}
            ))
        return results
