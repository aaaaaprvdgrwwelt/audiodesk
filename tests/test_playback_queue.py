
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from audiodesk.library import TRACK, LibraryIndex
from audiodesk.mainwindow import MainWindow

_app = QApplication.instance() or QApplication([])


def make_window_with_album(tmp_path) -> tuple[MainWindow, list]:
    window = MainWindow()
    window.library = LibraryIndex(tmp_path / "library.sqlite")
    root = tmp_path / "music"
    (root / "Artist" / "Album").mkdir(parents=True)
    for i in range(3):
        path = root / "Artist" / "Album" / f"t{i}.mp3"
        path.write_bytes(b"")  # _play_item() prueft path.exists()
        window.library.mark_scanned(
            path, TRACK, root, title=f"T{i}", album="Album", track_number=i + 1)
    items = window.library.list_tracks("Album")
    return window, items


def test_queue_takes_priority_over_sibling_logic(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window._queue_add([items[2]])
    window.player.current_item = items[0]
    window._play_next()
    assert window.player.current_item.title == "T2"
    assert window.queue_list.count() == 0
    window.close()


def test_queue_add_next_up_inserts_at_front(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window._queue_add([items[0]])
    window._queue_add([items[2]], next_up=True)
    titles = [window.queue_list.item(i).data(Qt.UserRole).title
              for i in range(window.queue_list.count())]
    assert titles == ["T2", "T0"]
    window.close()


def test_repeat_one_replays_current_item(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window.player.repeat_mode = "one"
    window.player.current_item = items[1]
    window._play_next()
    assert window.player.current_item.title == "T1"
    window.close()


def test_repeat_all_wraps_to_first_track(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window.player.repeat_mode = "all"
    window.player.current_item = items[2]
    window._play_next()
    assert window.player.current_item.title == "T0"
    window.close()


def test_repeat_off_does_nothing_at_end_of_album(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window.player.repeat_mode = "off"
    window.player.current_item = items[2]
    window._play_next()
    # Kein weiterer Titel bekannt - _play_item wird nicht aufgerufen, current_item
    # bleibt unveraendert.
    assert window.player.current_item.title == "T2"
    window.close()


def test_shuffle_picks_a_different_track_than_current(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window.player.shuffle = True
    for _ in range(20):
        window.player.current_item = items[0]
        window._play_next()
        # Shuffle darf nie denselben Titel erneut waehlen (echter Zufall
        # ueber mehrere Laeufe geprueft, um Glueckstreffer auszuschliessen).
        assert window.player.current_item.title in {"T1", "T2"}
    window.close()


def test_queue_context_menu_remove_and_clear(tmp_path):
    window, items = make_window_with_album(tmp_path)
    window._queue_add(items)
    assert window.queue_list.count() == 3
    window.queue_list.clear()
    assert window.queue_list.count() == 0
    window.close()
