"""Apples iTunes Search API als Hoerbuch-Quelle - oeffentlich, kostenlos,
kein API-Key noetig (https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/).

Anders als MusicBrainz/Discogs/Last.fm (reine Musikdatenbanken, siehe
`supports_track`) hat der iTunes Store eine eigene Hoerbuch-Kategorie
(`media=audiobook`) - das ist die einzige der eingebauten Quellen, die
`supports_chapter` setzt.
"""
from __future__ import annotations

import threading
import time

import requests

from deskkit.cache import ResponseCache

from .base import Candidate, MetadataProvider, SearchQuery, TrackInfo

API_BASE = "https://itunes.apple.com"
USER_AGENT = "AudioDesk/1.0 (+https://github.com/aaaaaprvdgrwwelt/audiodesk)"
MIN_INTERVAL = 0.4  # Apple begrenzt auf ca. 20 Anfragen/Minute ohne Key.


def _high_res(artwork_url: str | None) -> str | None:
    """iTunes liefert im Suchergebnis nur ein 100x100-Vorschaubild - die
    Groesse steckt aber direkt im Dateinamen und laesst sich hochsetzen."""
    if not artwork_url:
        return None
    return artwork_url.replace("100x100bb", "600x600bb")


class ItunesAudiobooksProvider(MetadataProvider):
    name = "itunes_audiobooks"
    label = "iTunes (Hoerbuecher)"
    supports_chapter = True

    def __init__(self):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._cache = ResponseCache("audiodesk", "itunes_audiobooks.sqlite")

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
        term = f"{query.title} {query.artist}".strip()
        params = {"term": term, "media": "audiobook", "limit": limit}
        data = self._get("/search", params)
        results = []
        for entry in data.get("results", [])[:limit]:
            year = None
            release = entry.get("releaseDate") or ""
            if len(release) >= 4 and release[:4].isdigit():
                year = int(release[:4])
            results.append(Candidate(
                source=self.name, external_id=str(entry.get("collectionId", "")),
                title=entry.get("collectionName") or "",
                # Der iTunes Store fuehrt bei Hoerbuechern meist den Autor
                # (nicht den Sprecher) als "artistName".
                artist=entry.get("artistName") or "", year=year,
                cover_url=_high_res(entry.get("artworkUrl100"))))
        return results

    def details(self, candidate: Candidate) -> TrackInfo:
        return TrackInfo(
            title=candidate.title, artist=candidate.artist, year=candidate.year,
            cover_url=candidate.cover_url, source=self.name,
            external_id=candidate.external_id)
