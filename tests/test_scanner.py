from pathlib import Path

from audiodesk.library import CHAPTER, TRACK, LibraryIndex
from audiodesk.scanner import ScanWorker, find_audio, scan_folder


def make_index(tmp_path) -> LibraryIndex:
    return LibraryIndex(tmp_path / "library.sqlite")


def test_find_audio_only_lists_known_extensions(tmp_path):
    (tmp_path / "song.mp3").write_bytes(b"")
    (tmp_path / "song.flac").write_bytes(b"")
    (tmp_path / "notes.txt").write_bytes(b"")
    found = find_audio(tmp_path)
    names = {p.name for p in found}
    assert names == {"song.mp3", "song.flac"}


def test_scan_folder_track_kind_scans_as_track(tmp_path):
    root = tmp_path / "music"
    folder = root / "Artist" / "Album"
    folder.mkdir(parents=True)
    (folder / "track1.mp3").write_bytes(b"")

    index = make_index(tmp_path)
    scan_folder(folder, root, TRACK, index)

    tracks = index.list_tracks()
    assert len(tracks) == 1
    assert tracks[0].path == str(folder / "track1.mp3")


def test_scan_folder_chapter_kind_scans_as_chapter_with_book_title_fallback(tmp_path):
    root = tmp_path / "audiobooks"
    folder = root / "Dune"
    folder.mkdir(parents=True)
    (folder / "chapter1.mp3").write_bytes(b"")

    index = make_index(tmp_path)
    scan_folder(folder, root, CHAPTER, index)

    chapters = index.list_chapters()
    assert len(chapters) == 1
    # Ohne Album-Tag faellt der Ordnername der Datei als Hoerbuchtitel ein.
    assert chapters[0].book_title == "Dune"


def test_scan_folder_only_touches_given_subfolder(tmp_path):
    root = tmp_path / "music"
    folder_a = root / "ArtistA"
    folder_b = root / "ArtistB"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    (folder_a / "a.mp3").write_bytes(b"")
    (folder_b / "b.mp3").write_bytes(b"")

    index = make_index(tmp_path)
    index.mark_scanned(folder_a / "a.mp3", TRACK, root, title="A")
    index.mark_scanned(folder_b / "b.mp3", TRACK, root, title="B")

    (folder_b / "b.mp3").unlink()
    scan_folder(folder_a, root, TRACK, index)

    remaining_titles = {t.title for t in index.list_tracks()}
    assert remaining_titles == {"A", "B"}


def make_tracks(root: Path, count: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (root / f"track{i}.mp3").write_bytes(b"")


def test_scan_worker_stop_halts_processing_mid_scan(tmp_path):
    root = tmp_path / "music"
    make_tracks(root, 20)
    library = make_index(tmp_path)
    worker = ScanWorker([str(root)], [], library)

    original = library.mark_scanned
    calls = []

    def counting(*args, **kwargs):
        calls.append(1)
        if len(calls) == 5:
            worker.stop()
        return original(*args, **kwargs)

    library.mark_scanned = counting
    worker.run()

    assert len(calls) == 5
    assert len(library.all_items()) == 5


def test_scan_worker_stop_does_not_wrongly_forget_existing_entries(tmp_path):
    root = tmp_path / "music"
    make_tracks(root, 10)
    library = make_index(tmp_path)
    ScanWorker([str(root)], [], library).run()
    assert len(library.all_items()) == 10

    worker = ScanWorker([str(root)], [], library)
    calls = []
    original = library.mark_scanned

    def counting(*args, **kwargs):
        calls.append(1)
        if len(calls) == 3:
            worker.stop()
        return original(*args, **kwargs)

    library.mark_scanned = counting
    worker.run()
    assert len(library.all_items()) == 10


def test_scan_folder_should_stop_halts_processing(tmp_path):
    root = tmp_path / "music"
    make_tracks(root, 10)
    library = make_index(tmp_path)
    calls = []

    def should_stop():
        calls.append(1)
        return len(calls) > 3

    scan_folder(root, root, TRACK, library, should_stop=should_stop)
    assert len(library.all_items()) == 3
