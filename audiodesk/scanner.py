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
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        for root in self.music_roots:
            if self._stop:
                break
            self.progress.emit(root)
            root_path = Path(root)
            found = find_audio(root_path)
            for path in found:
                if self._stop:
                    break
                tags = read_tags(path)
                self.library.mark_scanned(
                    path, TRACK, root_path, tags.title, tags.artist,
                    tags.album, tags.album_artist, tags.track_number,
                    tags.year, tags.genre, tags.duration_ms)
            # find_audio() lief vollstaendig, auch bei einem Abbruch mitten
            # in der Schleife darueber - das Aufraeumen bleibt deshalb sicher
            # auf tatsaechlich fehlende Dateien beschraenkt.
            self.library.forget_missing(root_path, {str(p) for p in found})

        for root in self.audiobook_roots:
            if self._stop:
                break
            self.progress.emit(root)
            root_path = Path(root)
            found = find_audio(root_path)
            for path in found:
                if self._stop:
                    break
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


def scan_folder(folder: Path, root: Path, kind: str, library: LibraryIndex,
                should_stop=None) -> None:
    """Nur `folder` neu einlesen - z. B. der Ordner eines einzelnen Albums
    oder Hoerbuchs, statt des ganzen Wurzelordners `root`. Eintraege werden
    weiterhin unter `root` gefuehrt (wie beim vollen Scan), aber nur
    unterhalb von `folder` verglichen/aufgeraeumt. `should_stop` ist ein
    parameterloses Callable, das True liefert, sobald abgebrochen werden
    soll (siehe FolderScanWorker.stop())."""
    should_stop = should_stop or (lambda: False)
    found = find_audio(folder)
    for path in found:
        if should_stop():
            break
        tags = read_tags(path)
        if kind == TRACK:
            library.mark_scanned(
                path, TRACK, root, tags.title, tags.artist,
                tags.album, tags.album_artist, tags.track_number,
                tags.year, tags.genre, tags.duration_ms)
        else:
            book_title = tags.album or path.parent.name
            library.mark_scanned(
                path, CHAPTER, root, tags.title, tags.artist,
                tags.album, tags.album_artist, tags.track_number,
                tags.year, tags.genre, tags.duration_ms, book_title)
    library.forget_missing_under(folder, {str(p) for p in found})


class FolderScanWorker(QObject):
    """Wie `ScanWorker`, aber fuer einen einzelnen Unterordner statt aller
    konfigurierten Wurzelordner - fuer den gezielten Scan aus dem
    Kontextmenue eines einzelnen Albums oder Hoerbuchs."""

    progress = Signal(str)
    finished = Signal()

    def __init__(self, folder: Path, root: Path, kind: str, library: LibraryIndex):
        super().__init__()
        self.folder = folder
        self.root = root
        self.kind = kind
        self.library = library
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        self.progress.emit(str(self.folder))
        scan_folder(self.folder, self.root, self.kind, self.library,
                   should_stop=lambda: self._stop)
        self.finished.emit()


def run_folder_in_thread(folder: Path, root: Path, kind: str, library: LibraryIndex):
    """Gibt (thread, worker) zurueck - der Aufrufer verbindet die Signale."""
    thread = QThread()
    worker = FolderScanWorker(folder, root, kind, library)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    return thread, worker
