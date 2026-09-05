"""Gemeinsame Schnittstelle fuer Metadaten-Quellen (Musik/Hoerbuecher)."""
from __future__ import annotations

from dataclasses import dataclass, field

from deskkit.matching import normalize_title, title_similarity

__all__ = [
    "normalize_title", "title_similarity", "artist_similarity",
    "ROLE_PRIMARY", "ROLE_SUPPLEMENT", "SearchQuery", "Candidate",
    "TrackInfo", "MetadataProvider",
]

#: Quellen, die einen Titel selbst bestimmen koennen.
ROLE_PRIMARY = "primary"
#: Quellen, die nur ergaenzen. Gewinnen nie allein.
ROLE_SUPPLEMENT = "supplement"


def artist_similarity(a: str, b: str) -> float:
    """Interpret/Autor-Aehnlichkeit - derselbe Algorithmus wie fuer Titel,
    eigener Name, weil er hier ein zweites, unabhaengiges Signal ist."""
    return title_similarity(a, b)


@dataclass
class SearchQuery:
    """Was wir aus den vorhandenen Tags bzw. dem Dateinamen wissen."""

    title: str
    artist: str = ""
    album: str = ""


@dataclass
class Candidate:
    """Ein Treffer einer Quelle, noch ohne volle Details."""

    source: str
    external_id: str
    title: str
    artist: str = ""
    album: str = ""
    year: int | None = None
    cover_url: str | None = None
    score: int = 0
    reasons: list[str] = field(default_factory=list)


@dataclass
class TrackInfo:
    """Volle Metadaten eines gewaehlten Treffers."""

    title: str
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    year: int | None = None
    cover_url: str | None = None
    source: str = ""
    external_id: str = ""


class MetadataProvider:
    """Basisklasse. `search` liefert Kandidaten, `details` vertieft."""

    name = "base"
    label = "Basis"
    role = ROLE_PRIMARY

    def available(self) -> tuple[bool, str]:
        """(nutzbar, Begruendung falls nicht)."""
        return False, "Nicht konfiguriert"

    def search(self, query: SearchQuery, limit: int = 10) -> list[Candidate]:
        raise NotImplementedError

    def details(self, candidate: Candidate) -> TrackInfo:
        """Volle Metadaten fuer den Gewinner - erst hier noetig."""
        return TrackInfo(
            title=candidate.title, artist=candidate.artist,
            album=candidate.album, year=candidate.year,
            cover_url=candidate.cover_url, source=candidate.source,
            external_id=candidate.external_id,
        )
