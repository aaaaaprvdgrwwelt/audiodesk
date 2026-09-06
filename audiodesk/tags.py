"""Audio-Tags lesen und schreiben - ueber mutagen, das MP3/ID3, MP4/M4B,
FLAC und OGG einheitlich abdeckt. Ein Modul statt eines Dateiformat-
Dispatch (anders als bei bookdesk mit EPUB/PDF), weil mutagen selbst schon
alle Formate hinter einer gemeinsamen Schnittstelle verbirgt.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mutagen
from mutagen.flac import Picture
from mutagen.mp4 import MP4

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".oga", ".opus", ".wav"}

#: M4B-Kapitelmarken stecken im "chpl"-Atom (Nero-Stil) - das einzige
#: Format, ueber das mutagen Kapitel liest (kein Text-Track-basiertes
#: QuickTime-Kapitelformat).
_MP4_EXTENSIONS = {".m4a", ".m4b"}

#: EasyID3/EasyMP4 & Co. liefern Listen von Strings je Schluessel.
_EASY_KEYS = {
    "title": "title", "artist": "artist", "album": "album",
    "albumartist": "album_artist", "genre": "genre",
}


@dataclass
class Chapter:
    title: str
    start_ms: int


@dataclass
class TrackTags:
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    track_number: int | None = None
    year: int | None = None
    genre: str = ""
    duration_ms: int = 0


def _first(easy_tags, key: str) -> str:
    if easy_tags is None:
        return ""
    values = easy_tags.get(key)
    return values[0] if values else ""


def read_tags(path: Path) -> TrackTags:
    try:
        easy = mutagen.File(str(path), easy=True)
    except Exception:  # noqa: BLE001
        easy = None
    if easy is None:
        return TrackTags(title=path.stem)

    values = {name: _first(easy, key) for key, name in _EASY_KEYS.items()}

    track_number = None
    raw_track = _first(easy, "tracknumber")
    if raw_track:
        try:
            track_number = int(raw_track.split("/")[0])
        except ValueError:
            pass

    year = None
    raw_date = _first(easy, "date") or _first(easy, "originaldate")
    digits = "".join(c for c in raw_date[:4] if c.isdigit())
    if len(digits) == 4:
        year = int(digits)

    duration_ms = 0
    if getattr(easy, "info", None) is not None:
        duration_ms = round((easy.info.length or 0) * 1000)

    return TrackTags(
        title=values["title"] or path.stem, artist=values["artist"],
        album=values["album"], album_artist=values["album_artist"],
        track_number=track_number, year=year, genre=values["genre"],
        duration_ms=duration_ms)


def read_chapters(path: Path) -> list[Chapter]:
    """Eingebettete Kapitelmarken, falls vorhanden - nur M4B/M4A (siehe
    _MP4_EXTENSIONS). Ohne "chpl"-Atom (die meisten M4B-Dateien ohne
    Nero-Kapitel, sowie jedes andere Format) leere Liste, kein Fehler -
    die Wiedergabe funktioniert dann einfach ohne Kapitelsprungmarken."""
    if path.suffix.lower() not in _MP4_EXTENSIONS:
        return []
    try:
        mp4 = MP4(str(path))
    except Exception:  # noqa: BLE001
        return []
    if not mp4.chapters:
        return []
    return [Chapter(title=c.title or "", start_ms=round(c.start * 1000))
            for c in mp4.chapters]


def write_tags(path: Path, tags: TrackTags) -> None:
    """Tags direkt in die Datei zurueckschreiben - ueber mutagens
    Easy-Schnittstelle, die fuer alle unterstuetzten Formate einheitlich
    funktioniert. Nur auf ausdruecklichen Nutzerwunsch aufrufen, nie
    automatisch beim Scannen/Zuordnen."""
    easy = mutagen.File(str(path), easy=True)
    if easy is None:
        raise ValueError(f"Konnte {path} nicht als Audiodatei oeffnen")

    easy["title"] = tags.title or ""
    easy["artist"] = tags.artist or ""
    easy["album"] = tags.album or ""
    easy["genre"] = tags.genre or ""
    if tags.track_number is not None:
        easy["tracknumber"] = str(tags.track_number)
    if tags.year is not None:
        easy["date"] = str(tags.year)
    # Nicht jedes Format kennt "albumartist" ueber die Easy-Schnittstelle
    # (z. B. manche OGG-Varianten) - dann bleibt das Feld einfach unbelegt.
    if tags.album_artist:
        try:
            easy["albumartist"] = tags.album_artist
        except (KeyError, ValueError):
            pass
    easy.save()


def cover_bytes(path: Path) -> bytes | None:
    """Eingebettetes Cover, je nach Format an anderer Stelle verstaut - kein
    einheitliches mutagen-Feld dafuer, deshalb Format-spezifisch."""
    try:
        raw = mutagen.File(str(path))
    except Exception:  # noqa: BLE001
        return None
    if raw is None:
        return None

    # ID3 (MP3): APIC-Frames.
    if hasattr(raw, "tags") and raw.tags is not None:
        for key in raw.tags.keys():
            if key.startswith("APIC"):
                return raw.tags[key].data

    # MP4 (M4A/M4B): 'covr' liefert MP4Cover-Objekte (bytes-aehnlich).
    covr = raw.get("covr") if hasattr(raw, "get") else None
    if covr:
        return bytes(covr[0])

    # FLAC: eigene Picture-Liste.
    pictures = getattr(raw, "pictures", None)
    if pictures:
        return pictures[0].data

    # OGG Vorbis/Opus: Base64-kodierter FLAC-Picture-Block.
    if hasattr(raw, "tags") and raw.tags is not None:
        block = raw.tags.get("metadata_block_picture")
        if block:
            import base64
            try:
                picture = Picture(base64.b64decode(block[0]))
                return picture.data
            except Exception:  # noqa: BLE001
                return None
    return None
