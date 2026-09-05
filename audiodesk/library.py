"""Bibliotheksindex: SQLite mit einer Zeile je Audiodatei.

Wie bei moviedesk/bookdesk (anders als comicdesk mit ComicInfo.xml *in* der
Datei) ist diese Datenbank die Quelle der Wahrheit fuer Zuordnungen und
Wiedergabefortschritt.
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

TRACK = "track"
CHAPTER = "chapter"

STATUS_MATCHED = "matched"
STATUS_UNSURE = "unsure"
STATUS_UNMATCHED = "unmatched"
STATUS_ERROR = "error"

#: `book_title` ist nur bei kind=CHAPTER belegt - der Name des Hoerbuchs,
#: zu dem diese Datei gehoert.
SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    root TEXT NOT NULL,
    title TEXT DEFAULT '',
    artist TEXT DEFAULT '',
    album TEXT DEFAULT '',
    album_artist TEXT DEFAULT '',
    track_number INTEGER,
    year INTEGER,
    genre TEXT DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    cover_path TEXT,
    book_title TEXT DEFAULT '',
    source TEXT DEFAULT '',
    external_id TEXT DEFAULT '',
    score INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'unmatched',
    note TEXT DEFAULT '',
    last_position_ms INTEGER DEFAULT 0,
    scanned_at REAL,
    matched_at REAL
)
"""


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    path = Path(base) / "audiodesk"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class Item:
    id: int
    kind: str
    path: str
    root: str
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    track_number: int | None = None
    year: int | None = None
    genre: str = ""
    duration_ms: int = 0
    cover_path: str | None = None
    book_title: str = ""
    source: str = ""
    external_id: str = ""
    score: int = 0
    status: str = STATUS_UNMATCHED
    note: str = ""
    last_position_ms: int = 0

    @property
    def display_title(self) -> str:
        year = f" ({self.year})" if self.year else ""
        return f"{self.title}{year}"

    @property
    def source_url(self) -> str | None:
        if self.source == "musicbrainz" and self.external_id:
            kind = "release-group" if self.kind == TRACK else "recording"
            return f"https://musicbrainz.org/{kind}/{self.external_id}"
        return None


_COLUMNS = [
    "id", "kind", "path", "root", "title", "artist", "album", "album_artist",
    "track_number", "year", "genre", "duration_ms", "cover_path",
    "book_title", "source", "external_id", "score", "status", "note",
    "last_position_ms",
]


def _row_to_item(row: sqlite3.Row) -> Item:
    data = dict(row)
    return Item(**{k: data.get(k) for k in _COLUMNS})


class LibraryIndex:
    def __init__(self, path: Path | None = None):
        self._path = path or (data_dir() / "library.sqlite")
        self._con = sqlite3.connect(str(self._path), check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._con.execute(SCHEMA)
            self._con.commit()

    def close(self) -> None:
        self._con.close()

    # --- Scannen --------------------------------------------------------
    def mark_scanned(self, path: Path, kind: str, root: Path, title: str = "",
                     artist: str = "", album: str = "", album_artist: str = "",
                     track_number: int | None = None, year: int | None = None,
                     genre: str = "", duration_ms: int = 0,
                     book_title: str = "") -> None:
        """Datei bekannt machen, falls neu - vorhandene Zuordnung bleibt."""
        with self._lock:
            self._con.execute(
                "INSERT INTO items (kind, path, root, title, artist, album, "
                "album_artist, track_number, year, genre, duration_ms, "
                "book_title, scanned_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(path) DO UPDATE SET scanned_at=excluded.scanned_at",
                (kind, str(path), str(root), title, artist, album, album_artist,
                 track_number, year, genre, duration_ms, book_title, time.time()))
            self._con.commit()

    def forget_missing(self, root: Path, existing: set[str]) -> int:
        """Eintraege loeschen, deren Datei unter `root` nicht mehr da ist."""
        with self._lock:
            rows = self._con.execute(
                "SELECT path FROM items WHERE root=?", (str(root),)).fetchall()
            gone = [r["path"] for r in rows if r["path"] not in existing]
            if gone:
                self._con.executemany(
                    "DELETE FROM items WHERE path=?", [(p,) for p in gone])
                self._con.commit()
            return len(gone)

    def remove_path(self, path: Path) -> None:
        with self._lock:
            self._con.execute("DELETE FROM items WHERE path=?", (str(path),))
            self._con.commit()

    def remove_under(self, folder: Path) -> None:
        """Alle Eintraege unterhalb `folder` entfernen - nach Loeschen des
        ganzen Verzeichnisses."""
        prefix = str(folder).rstrip("/") + "/"
        with self._lock:
            self._con.execute(
                "DELETE FROM items WHERE path LIKE ? ESCAPE '\\'",
                (prefix.replace("%", "\\%").replace("_", "\\_") + "%",))
            self._con.commit()

    # --- Zuordnung --------------------------------------------------------
    def set_match(self, path: Path, title: str, artist: str, album: str,
                  album_artist: str, year: int | None, cover_path: str | None,
                  source: str, external_id: str, score: int, status: str,
                  note: str = "") -> None:
        with self._lock:
            self._con.execute(
                "UPDATE items SET title=?, artist=?, album=?, album_artist=?, "
                "year=?, cover_path=?, source=?, external_id=?, score=?, "
                "status=?, note=?, matched_at=? WHERE path=?",
                (title, artist, album, album_artist, year, cover_path, source,
                 external_id, score, status, note, time.time(), str(path)))
            self._con.commit()

    def set_status(self, path: Path, status: str, note: str = "") -> None:
        with self._lock:
            self._con.execute(
                "UPDATE items SET status=?, note=? WHERE path=?",
                (status, note, str(path)))
            self._con.commit()

    def set_cover_path(self, path: Path, cover_path: str) -> None:
        with self._lock:
            self._con.execute(
                "UPDATE items SET cover_path=? WHERE path=?",
                (cover_path, str(path)))
            self._con.commit()

    def set_last_position_ms(self, path: Path, position_ms: int) -> None:
        with self._lock:
            self._con.execute(
                "UPDATE items SET last_position_ms=? WHERE path=?",
                (position_ms, str(path)))
            self._con.commit()

    def update_path(self, old: Path, new: Path) -> None:
        with self._lock:
            self._con.execute(
                "UPDATE items SET path=? WHERE path=?", (str(new), str(old)))
            self._con.commit()

    # --- Lesen --------------------------------------------------------
    def get(self, path: Path) -> Item | None:
        with self._lock:
            row = self._con.execute(
                "SELECT * FROM items WHERE path=?", (str(path),)).fetchone()
        return _row_to_item(row) if row else None

    def list_tracks(self, album: str | None = None) -> list[Item]:
        with self._lock:
            if album is None:
                rows = self._con.execute(
                    "SELECT * FROM items WHERE kind=? "
                    "ORDER BY artist COLLATE NOCASE, album COLLATE NOCASE, "
                    "track_number", (TRACK,)).fetchall()
            else:
                rows = self._con.execute(
                    "SELECT * FROM items WHERE kind=? AND album=? "
                    "ORDER BY track_number, title COLLATE NOCASE",
                    (TRACK, album)).fetchall()
        return [_row_to_item(r) for r in rows]

    def albums(self) -> list[tuple[str, int]]:
        with self._lock:
            rows = self._con.execute(
                "SELECT album AS name, COUNT(*) AS n FROM items "
                "WHERE kind=? AND album != '' GROUP BY album "
                "ORDER BY album COLLATE NOCASE", (TRACK,)).fetchall()
        return [(r["name"], r["n"]) for r in rows]

    def list_chapters(self) -> list[Item]:
        with self._lock:
            rows = self._con.execute(
                "SELECT * FROM items WHERE kind=? "
                "ORDER BY book_title COLLATE NOCASE, track_number",
                (CHAPTER,)).fetchall()
        return [_row_to_item(r) for r in rows]

    def audiobook_groups(self) -> list[tuple[str, list[Item]]]:
        """Kapitel nach Hoerbuchtitel gruppiert (Gross-/Kleinschreibung egal,
        siehe die entsprechende Loesung in moviedesk/library.py)."""
        by_key: dict[str, list[Item]] = {}
        for item in self.list_chapters():
            key = (item.book_title or "?").casefold()
            by_key.setdefault(key, []).append(item)
        groups = [
            (next((i.book_title for i in items if i.source), None)
             or items[0].book_title or "?", items)
            for items in by_key.values()
        ]
        return sorted(groups, key=lambda kv: kv[0].casefold())

    def unresolved(self) -> list[Item]:
        with self._lock:
            rows = self._con.execute(
                "SELECT * FROM items WHERE status IN (?, ?) "
                "ORDER BY path", (STATUS_UNSURE, STATUS_UNMATCHED)).fetchall()
        return [_row_to_item(r) for r in rows]

    def all_items(self) -> list[Item]:
        with self._lock:
            rows = self._con.execute("SELECT * FROM items ORDER BY path").fetchall()
        return [_row_to_item(r) for r in rows]
