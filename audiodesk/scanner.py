"""Bibliotheksordner einlesen: Audiodateien finden, Tags lesen.

Musik- und Hoerbuch-Ordner werden getrennt gefuehrt (wie moviedesks
movie_roots/series_roots) - das entscheidet zuverlaessig, ob eine Datei als
TRACK (zu einem Album) oder CHAPTER (zu einem Hoerbuch) gilt, ohne auf eine
fehleranfaellige automatische Erkennung angewiesen zu sein.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from .library import CHAPTER, LibraryIndex, TRACK
from .tags import AUDIO_EXTENSIONS, read_tags


def find_audio(root: Path) -> list[Path]:
    """Alle Audiodateien unter `root`."""
    if not root.is_dir():
        return []
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        found.append(path)
    found.sort(key=lambda p: str(p).casefold())
    return found


class ScanWorker(QObject):
    """Laeuft im eigenen Thread - Verzeichnisse koennen gross sein, die
    Oberflaeche soll dabei nicht einfrieren."""

    progress = Signal(str)   # aktuell durchsuchter Ordner
    finished = Signal()

    def __init__(self, music_roots: list[str], audiobook_roots: list[str],
                library: LibraryIndex):
        super().__init__()
        self.music_roots = music_roots
        self.audiobook_roots = audiobook_roots
        self.library = library

    def run(self) -> None:
        for root in self.music_roots:
            self.progress.emit(root)
            root_path = Path(root)
            found = find_audio(root_path)
            for path in found:
                tags = read_tags(path)
                self.library.mark_scanned(
                    path, TRACK, root_path, tags.title, tags.artist,
                    tags.album, tags.album_artist, tags.track_number,
                    tags.year, tags.genre, tags.duration_ms)
            self.library.forget_missing(root_path, {str(p) for p in found})

        for root in self.audiobook_roots:
            self.progress.emit(root)
            root_path = Path(root)
            found = find_audio(root_path)
            for path in found:
                tags = read_tags(path)
                # Der Hoerbuchtitel steht meist im Album-Tag; ohne den faellt
                # der Ordnername der Datei als Rueckfall ein.
                book_title = tags.album or path.parent.name
                self.library.mark_scanned(
                    path, CHAPTER, root_path, tags.title, tags.artist,
                    tags.album, tags.album_artist, tags.track_number,
                    tags.year, tags.genre, tags.duration_ms, book_title)
            self.library.forget_missing(root_path, {str(p) for p in found})
        self.finished.emit()


def run_in_thread(music_roots: list[str], audiobook_roots: list[str],
                  library: LibraryIndex):
    """Gibt (thread, worker) zurueck - der Aufrufer verbindet die Signale."""
    thread = QThread()
    worker = ScanWorker(music_roots, audiobook_roots, library)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    return thread, worker
