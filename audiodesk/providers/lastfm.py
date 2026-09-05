"""Last.fm als Metadaten-Quelle - braucht einen kostenlosen API-Key
(last.fm/api/account/create)."""
from __future__ import annotations

import threading
import time

import requests

from deskkit.cache import ResponseCache

from ..i18n import _
from .base import Candidate, MetadataProvider, SearchQuery, TrackInfo

API_BASE = "https://ws.audioscrobbler.com/2.0/"
MIN_INTERVAL = 0.25


class LastFmProvider(MetadataProvider):
    name = "lastfm"
    label = "Last.fm"
    supports_track = True

    def __init__(self, api_key: str):
        self.api_key = (api_key or "").strip()
        self._session = requests.Session()
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._cache = ResponseCache("audiodesk", "lastfm.sqlite")

    def available(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, _("Kein API-Key hinterlegt.")
        return True, ""

    def _get(self, params: dict) -> dict:
        key = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        with self._lock:
            wait = MIN_INTERVAL - (time.time() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            response = self._session.get(
                API_BASE,
                params={**params, "api_key": self.api_key, "format": "json"},
                timeout=15)
            self._last_call = time.time()
        response.raise_for_status()
        data = response.json()
        self._cache.put(key, data)
        return data

    def search(self, query: SearchQuery, limit: int = 10) -> list[Candidate]:
        params = {"method": "track.search", "track": query.title, "limit": limit}
        if query.artist:
            params["artist"] = query.artist
        data = self._get(params)
        tracks = (data.get("results", {}).get("trackmatches", {}) or {}).get(
            "track", [])
        if isinstance(tracks, dict):  # Last.fm liefert bei genau einem Treffer
            tracks = [tracks]         # ein Objekt statt einer Liste.
        results = []
        for entry in tracks[:limit]:
            results.append(Candidate(
                source=self.name, external_id=entry.get("mbid") or "",
                title=entry.get("name") or "", artist=entry.get("artist") or ""))
        return results

    def details(self, candidate: Candidate) -> TrackInfo:
        """track.getInfo liefert (falls vorhanden) Album und Cover nach -
        die Trefferliste allein hat davon keins."""
        params = {"method": "track.getInfo", "track": candidate.title,
                  "artist": candidate.artist}
        try:
            data = self._get(params)
        except requests.RequestException:
            data = {}
        track = data.get("track") or {}
        album = track.get("album") or {}
        cover_url = None
        for image in album.get("image", []):
            if image.get("size") in ("extralarge", "large") and image.get("#text"):
                cover_url = image["#text"]
                if image.get("size") == "extralarge":
                    break
        return TrackInfo(
            title=candidate.title, artist=candidate.artist,
            album=album.get("title", ""), cover_url=cover_url,
            source=self.name, external_id=candidate.external_id)
