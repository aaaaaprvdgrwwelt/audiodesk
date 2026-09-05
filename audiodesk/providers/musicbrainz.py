"""MusicBrainz als Metadaten-Quelle - kostenlos, kein API-Key noetig.

Verlangt laut API-Richtlinie einen aussagekraeftigen User-Agent mit Kontakt
und ein striktes Rate-Limit (1 Anfrage/Sekunde) - beides hier
beruecksichtigt. Deckt Musik gut ab; die Hoerbuch-Abdeckung ist deutlich
luecklicher, da MusicBrainz in erster Linie eine Musikdatenbank ist (siehe
Hilfe-Dialog).
"""
from __future__ import annotations

import threading
import time

import requests

from deskkit.cache import ResponseCache

from .base import Candidate, MetadataProvider, SearchQuery, TrackInfo

API_BASE = "https://musicbrainz.org/ws/2"
COVER_BASE = "https://coverartarchive.org/release"
USER_AGENT = "AudioDesk/1.0 (+https://github.com/aaaaaprvdgrwwelt/audiodesk)"
MIN_INTERVAL = 1.0


class MusicBrainzProvider(MetadataProvider):
    name = "musicbrainz"
    label = "MusicBrainz"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._cache = ResponseCache("audiodesk", "musicbrainz.sqlite")

    def available(self) -> tuple[bool, str]:
        return True, ""

    def _get(self, path: str, params: dict) -> dict:
        key = path + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        with self._lock:
            wait = MIN_INTERVAL - (time.time() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            response = self._session.get(API_BASE + path, params=params, timeout=15)
            self._last_call = time.time()
        response.raise_for_status()
        data = response.json()
        self._cache.put(key, data)
        return data

    def search(self, query: SearchQuery, limit: int = 10) -> list[Candidate]:
        parts = [f'recording:"{query.title}"']
        if query.artist:
            parts.append(f'artist:"{query.artist}"')
        params = {"query": " AND ".join(parts), "fmt": "json", "limit": limit}
        data = self._get("/recording", params)
        results = []
        for rec in data.get("recordings", [])[:limit]:
            artist = ", ".join(
                c.get("name", "") for c in rec.get("artist-credit", []) if c.get("name"))
            releases = rec.get("releases") or []
            release = releases[0] if releases else {}
            album = release.get("title", "")
            year = None
            date = release.get("date", "") or ""
            if len(date) >= 4 and date[:4].isdigit():
                year = int(date[:4])
            cover_url = (
                f"{COVER_BASE}/{release['id']}/front" if release.get("id") else None)
            results.append(Candidate(
                source=self.name, external_id=rec.get("id", ""),
                title=rec.get("title", "") or "", artist=artist, album=album,
                year=year, cover_url=cover_url))
        return results

    def details(self, candidate: Candidate) -> TrackInfo:
        return TrackInfo(
            title=candidate.title, artist=candidate.artist,
            album=candidate.album, year=candidate.year,
            cover_url=candidate.cover_url, source=self.name,
            external_id=candidate.external_id)
