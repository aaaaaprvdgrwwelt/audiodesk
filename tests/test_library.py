from pathlib import Path

from audiodesk.library import CHAPTER, STATUS_MATCHED, TRACK, LibraryIndex


def make_index(tmp_path) -> LibraryIndex:
    return LibraryIndex(tmp_path / "library.sqlite")


def test_mark_scanned_inserts_track(tmp_path):
    index = make_index(tmp_path)
    index.mark_scanned(Path("/music/song.mp3"), TRACK, Path("/music"),
                       title="Get Lucky", artist="Daft Punk", album="RAM")
    tracks = index.list_tracks()
    assert len(tracks) == 1
    assert tracks[0].title == "Get Lucky"
    assert tracks[0].album == "RAM"


def test_backup_to_copies_all_items(tmp_path):
    index = make_index(tmp_path)
    index.mark_scanned(Path("/music/song.mp3"), TRACK, Path("/music"), title="Test")
    destination = tmp_path / "backup" / "copy.sqlite"
    index.backup_to(destination)
    assert destination.exists()

    restored = LibraryIndex(destination)
    assert [t.title for t in restored.list_tracks()] == ["Test"]


def test_mark_scanned_keeps_existing_match_on_rescan(tmp_path):
    index = make_index(tmp_path)
    path = Path("/music/song.mp3")
    index.mark_scanned(path, TRACK, Path("/music"), title="Get Lucky")
    index.set_match(path, "Get Lucky", "Daft Punk", "RAM", "Daft Punk", 2013,
                    None, "musicbrainz", "mbid1", 95, STATUS_MATCHED)
    index.mark_scanned(path, TRACK, Path("/music"), title="Get Lucky")
    tracks = index.list_tracks()
    assert len(tracks) == 1
    assert tracks[0].status == STATUS_MATCHED
    assert tracks[0].artist == "Daft Punk"


def test_forget_missing_removes_gone_files(tmp_path):
    index = make_index(tmp_path)
    root = Path("/music")
    index.mark_scanned(root / "a.mp3", TRACK, root, title="A")
    index.mark_scanned(root / "b.mp3", TRACK, root, title="B")
    removed = index.forget_missing(root, {str(root / "a.mp3")})
    assert removed == 1
    assert [t.title for t in index.list_tracks()] == ["A"]


def test_albums_groups_tracks_by_album_name(tmp_path):
    index = make_index(tmp_path)
    root = Path("/music")
    index.mark_scanned(root / "1.mp3", TRACK, root, title="T1", album="RAM")
    index.mark_scanned(root / "2.mp3", TRACK, root, title="T2", album="RAM")
    index.mark_scanned(root / "3.mp3", TRACK, root, title="T3", album="Discovery")
    albums = dict(index.albums())
    assert albums == {"RAM": 2, "Discovery": 1}


def test_albums_excludes_tracks_without_album(tmp_path):
    index = make_index(tmp_path)
    root = Path("/music")
    index.mark_scanned(root / "1.mp3", TRACK, root, title="Standalone")
    assert index.albums() == []


def test_list_tracks_filters_by_album(tmp_path):
    index = make_index(tmp_path)
    root = Path("/music")
    index.mark_scanned(root / "1.mp3", TRACK, root, title="T1", album="RAM")
    index.mark_scanned(root / "2.mp3", TRACK, root, title="T2", album="Discovery")
    tracks = index.list_tracks(album="RAM")
    assert [t.title for t in tracks] == ["T1"]


def test_audiobook_groups_are_case_insensitive(tmp_path):
    # Regressionstest: dieselbe Loesung wie bei moviedesk.series_groups
    # ("futurama" vs. "Futurama") - hier fuer Hoerbuch-Titel.
    index = make_index(tmp_path)
    root = Path("/audiobooks")
    index.mark_scanned(root / "1.mp3", CHAPTER, root, title="Chapter 1",
                       book_title="dune")
    index.mark_scanned(root / "2.mp3", CHAPTER, root, title="Chapter 2",
                       book_title="Dune")
    groups = index.audiobook_groups()
    assert len(groups) == 1
    assert len(groups[0][1]) == 2


def test_audiobook_groups_prefers_book_title_of_matched_item(tmp_path):
    # set_match aendert book_title selbst nicht - der Anzeigename kommt vom
    # ersten Eintrag mit gesetzter `source`, unabhaengig von der Reihenfolge.
    index = make_index(tmp_path)
    root = Path("/audiobooks")
    p1 = root / "1.mp3"
    p2 = root / "2.mp3"
    index.mark_scanned(p1, CHAPTER, root, title="Chapter 1", book_title="dune")
    index.mark_scanned(p2, CHAPTER, root, title="Chapter 2", book_title="Dune")
    index.set_match(p2, "Chapter 2", "Frank Herbert", "Dune", "", 1965,
                    None, "itunes_audiobooks", "id1", 90, STATUS_MATCHED)
    groups = index.audiobook_groups()
    assert groups[0][0] == "Dune"


def test_forget_missing_under_only_touches_given_folder(tmp_path):
    index = make_index(tmp_path)
    root = Path("/music")
    index.mark_scanned(root / "ArtistA" / "1.mp3", TRACK, root, title="A1")
    index.mark_scanned(root / "ArtistB" / "1.mp3", TRACK, root, title="B1")
    removed = index.forget_missing_under(root / "ArtistA", set())
    assert removed == 1
    remaining_titles = {t.title for t in index.list_tracks()}
    assert remaining_titles == {"B1"}


def test_remove_under_deletes_only_matching_prefix(tmp_path):
    index = make_index(tmp_path)
    root = Path("/music")
    index.mark_scanned(root / "artistA" / "1.mp3", TRACK, root, title="A1")
    index.mark_scanned(root / "artistB" / "1.mp3", TRACK, root, title="B1")
    index.remove_under(root / "artistA")
    remaining = {t.title for t in index.list_tracks()}
    assert remaining == {"B1"}
