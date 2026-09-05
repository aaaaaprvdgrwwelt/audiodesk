import shutil
import subprocess
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from audiodesk.library import CHAPTER, LibraryIndex
from audiodesk.player import PlayerBar
from audiodesk.tags import read_chapters

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg nicht installiert")

_app = QApplication.instance() or QApplication([])


def make_m4b_with_chapters(tmp_path) -> Path:
    """Ein winziges M4B mit zwei Nero-Kapitelmarken (chpl-Atom) - erzeugt
    ueber ffmpeg statt gemockt, damit der Test das echte Format prueft,
    das mutagen.mp4.MP4.chapters ausliest."""
    meta = tmp_path / "chapters.txt"
    meta.write_text(
        ";FFMETADATA1\n"
        "[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=5000\ntitle=Chapter One\n"
        "[CHAPTER]\nTIMEBASE=1/1000\nSTART=5000\nEND=10000\ntitle=Chapter Two\n",
        "utf-8")
    path = tmp_path / "book.m4b"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=10",
         "-i", str(meta), "-map_metadata", "1", "-c:a", "aac", str(path)],
        check=True, capture_output=True)
    return path


def test_read_chapters_extracts_nero_style_chpl_atom(tmp_path):
    path = make_m4b_with_chapters(tmp_path)
    chapters = read_chapters(path)
    assert [c.title for c in chapters] == ["Chapter One", "Chapter Two"]
    assert [c.start_ms for c in chapters] == [0, 5000]


def test_read_chapters_empty_for_file_without_chapters(tmp_path):
    path = tmp_path / "plain.m4a"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-c:a", "aac", str(path)], check=True, capture_output=True)
    assert read_chapters(path) == []


def test_read_chapters_empty_for_non_mp4_format(tmp_path):
    path = tmp_path / "song.mp3"
    path.write_bytes(b"")
    assert read_chapters(path) == []


def make_index_with_item(tmp_path, path: Path):
    library = LibraryIndex(tmp_path / "library.sqlite")
    library.mark_scanned(path, CHAPTER, tmp_path, title="Book", book_title="Book")
    return library, library.get(path)


def test_player_populates_chapter_combo_on_play(tmp_path):
    path = make_m4b_with_chapters(tmp_path)
    library, item = make_index_with_item(tmp_path, path)
    bar = PlayerBar(library)
    bar.play(item)
    assert [bar.chapter_combo.itemText(i) for i in range(bar.chapter_combo.count())] \
        == ["Chapter One", "Chapter Two"]
    assert bar.chapter_combo.isHidden() is False


def test_player_hides_chapter_combo_without_chapters(tmp_path):
    path = tmp_path / "plain.m4a"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-c:a", "aac", str(path)], check=True, capture_output=True)
    library, item = make_index_with_item(tmp_path, path)
    bar = PlayerBar(library)
    bar.play(item)
    assert bar.chapter_combo.isHidden() is True


def test_player_current_chapter_index_tracks_position(tmp_path):
    path = make_m4b_with_chapters(tmp_path)
    library, item = make_index_with_item(tmp_path, path)
    bar = PlayerBar(library)
    bar.play(item)
    assert bar._current_chapter_index(0) == 0
    assert bar._current_chapter_index(4999) == 0
    assert bar._current_chapter_index(5000) == 1
    assert bar._current_chapter_index(9000) == 1


def test_player_choosing_chapter_seeks_to_its_start(tmp_path):
    # QMediaPlayer.position() liesst sich hier nicht verlaesslich zurueck -
    # ohne echtes Audio-Backend laedt das offscreen-Qt die Datei nicht
    # tatsaechlich, setPosition() wirkt dann nicht. Stattdessen pruefen,
    # dass setPosition() mit der richtigen Kapitel-Startzeit aufgerufen wird.
    path = make_m4b_with_chapters(tmp_path)
    library, item = make_index_with_item(tmp_path, path)
    bar = PlayerBar(library)
    bar.play(item)
    calls = []
    bar._player.setPosition = calls.append
    bar._on_chapter_chosen(1)
    assert calls == [5000]
