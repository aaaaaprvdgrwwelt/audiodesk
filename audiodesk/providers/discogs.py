"""Discogs als Metadaten-Quelle - braucht einen kostenlosen persoenlichen
Zugriffs-Token (discogs.com/settings/developers)."""
from __future__ import annotations

import threading
import time

import requests

from deskkit.cache import ResponseCache

from ..i18n import _
from .base import Candidate, MetadataProvider, SearchQuery, TrackInfo

API_BASE = "https://api.discogs.com"
USER_AGENT = "AudioDesk/1.0 (+https://github.com/aaaaaprvdgrwwelt/audiodesk)"
MIN_INTERVAL = 1.1  # Discogs erlaubt 60 authentifizierte Anfragen/Minute.


class DiscogsProvider(MetadataProvider):
    name = "discogs"
    label = "Discogs"

    def __init__(self, token: str):
        self.token = (token or "").strip()
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._cache = ResponseCache("audiodesk", "discogs.sqlite")

    def available(self) -> tuple[bool, str]:
        if not self.token:
            return False, _("Kein API-Key hinterlegt.")
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
            response = self._session.get(
                API_BASE + path, params={**params, "token": self.token}, timeout=15)
            self._last_call = time.time()
        response.raise_for_status()
        data = response.json()
        self._cache.put(key, data)
        return data

    def search(self, query: SearchQuery, limit: int = 10) -> list[Candidate]:
        params = {"q": query.title, "type": "release", "per_page": limit}
        if query.artist:
            params["artist"] = query.artist
        data = self._get("/database/search", params)
        results = []
        for entry in data.get("results", [])[:limit]:
            # Discogs liefert Release-Titel als "Interpret - Titel" statt
            # getrennter Felder - bestmoegliche Aufteilung am ersten " - ".
            raw_title = entry.get("title") or ""
            if " - " in raw_title:
                artist, title = raw_title.split(" - ", 1)
            else:
                artist, title = "", raw_title
            year = None
            raw_year = entry.get("year")
            if raw_year and str(raw_year).isdigit():
                year = int(raw_year)
            cover = entry.get("cover_image") or entry.get("thumb") or None
            results.append(Candidate(
                source=self.name, external_id=str(entry.get("id", "")),
                title=title.strip(), artist=artist.strip(), year=year,
                cover_url=cover))
        return results

    def details(self, candidate: Candidate) -> TrackInfo:
        return TrackInfo(
            title=candidate.title, artist=candidate.artist,
            year=candidate.year, cover_url=candidate.cover_url,
            source=self.name, external_id=candidate.external_id)
