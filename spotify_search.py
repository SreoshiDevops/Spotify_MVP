import base64
import os
from typing import Any, Dict, List, Optional

import requests


class SpotifySearcher:
    """Handles Spotify API authentication and track search."""

    AUTH_URL = "https://accounts.spotify.com/api/token"
    SEARCH_URL = "https://api.spotify.com/v1/search"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token: Optional[str] = None
        if self.client_id and self.client_secret:
            self._authenticate()

    def _authenticate(self) -> None:
        if not self.client_id or not self.client_secret:
            return
        try:
            auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            response = requests.post(
                self.AUTH_URL,
                headers={"Authorization": f"Basic {auth}"},
                data={"grant_type": "client_credentials"},
                timeout=10,
            )
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
            else:
                self.access_token = None
        except Exception:
            self.access_token = None

    def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.access_token:
            self._authenticate()
        if not self.access_token:
            return []
        try:
            response = requests.get(
                self.SEARCH_URL,
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"q": query, "type": "track", "limit": min(limit, 20)},
                timeout=10,
            )
            if response.status_code == 401:
                self._authenticate()
                return self.search_tracks(query, limit)
            if response.status_code != 200:
                return []
            items = response.json().get("tracks", {}).get("items", [])
            return self._format_tracks(items)
        except Exception:
            return []

    def search_by_intent(self, intent: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        parts: List[str] = []
        for key in ["artist", "genre", "mood", "activity", "language"]:
            value = intent.get(key)
            if value:
                parts.append(str(value))
        query = " ".join(parts).strip() or "popular"
        return self.search_tracks(query, limit=limit)

    def _format_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for track in tracks:
            album = track.get("album", {})
            images = album.get("images", [])
            formatted.append(
                {
                    "id": track.get("id"),
                    "name": track.get("name"),
                    "artist": ", ".join(artist["name"] for artist in track.get("artists", [])),
                    "artists": [artist["name"] for artist in track.get("artists", [])],
                    "album": album.get("name"),
                    "image": images[0]["url"] if images else None,
                    "spotify_url": track.get("external_urls", {}).get("spotify"),
                    "preview_url": track.get("preview_url"),
                    "popularity": track.get("popularity"),
                    "duration_ms": track.get("duration_ms"),
                }
            )
        return formatted


def search_music(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    return SpotifySearcher().search_tracks(query, limit)
