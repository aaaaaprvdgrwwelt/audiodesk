"""Hauptfenster: Musik-/Hoerbuch-Raster, Scan, Wiedergabe, Umbenennen."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMessageBox, QProgressDialog, QSizePolicy, QSplitter,
    QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QToolBar, QToolButton, QVBoxLayout, QWidget,
)
from send2trash import send2trash

from deskkit.actions import ActionRegistry
from deskkit.paths import subfolder_of
from deskkit.tiles import STATUS_ROLE, SUBTITLE_ROLE, CoverDelegate, configure_grid

from . import matcher, renamer, scanner
from .appicon import icon as app_icon
from .config import Settings
from .helpdialog import HelpDialog
from .i18n import _, set_language
from .icons import icon as tool_icon
from .library import CHAPTER, Item, LibraryIndex, TRACK
from .matchdialog import MatchDialog
from .metapanel import MetaPanel
from .player import PlayerBar
from .renamedialog import RenameDialog
from .settingsdialog import SettingsDialog
from .tags import TrackTags
from .tags import write_tags as write_track_tags
from .thumbs import CoverLoader

TILE_W = 140
COVER_H = 190

STATUS_LABEL = {
    "matched": _("zugeordnet"),
    "unsure": _("unsicher"),
    "unmatched": _("nicht zugeordnet"),
    "error": _("Fehler"),
}
STATUS_COLOR = {
    "matched": QColor(46, 160, 90),
    "unsure": QColor(214, 154, 40),
    "unmatched": QColor(150, 150, 150),
    "error": QColor(192, 57, 43),
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioDesk")
        self.setWindowIcon(app_icon())
        self.resize(1200, 760)

        self.qsettings = QSettings("audiodesk", "audiodesk")
        self.settings = Settings.load(self.qsettings)
        set_language(self.settings.language)

        self.library = LibraryIndex()
        self.loader = CoverLoader(self)
        self.loader.ready.connect(self._on_cover)
        self.player = PlayerBar(self.library, self)
        self.player.finished.connect(self._play_next)

        self._search_text = ""
        self._build_central()
        self._build_actions()
        self._build_toolbar()
        self._build_menubar()
        self.setStatusBar(QStatusBar())

        self.refresh_view()

    # ------------------------------------------------------------------
    def _configure_grid(self, widget: QListWidget) -> None:
        configure_grid(widget, CoverDelegate(
            STATUS_COLOR, tile_w=TILE_W, cover_h=COVER_H, parent=widget))

    def _build_central(self) -> None:
        self.tabs = QTabWidget()

        # --- Musik ----------------------------------------------------
        self.album_list = QListWidget()
        self.album_list.itemSelectionChanged.connect(self._on_album_selected)

        self.track_list = QListWidget()
        self._configure_grid(self.track_list)
        self.track_list.itemSelectionChanged.connect(self._on_track_selected)
        self.track_list.itemDoubleClicked.connect(lambda _i: self.play_selected())
        self.track_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.track_list.customContextMenuRequested.connect(self._track_context_menu)

        self.track_meta = MetaPanel(self.loader)
        music_split = QSplitter()
        music_split.addWidget(self.album_list)
        music_split.addWidget(self.track_list)
        music_split.addWidget(self.track_meta)
        music_split.setStretchFactor(0, 1)
        music_split.setStretchFactor(1, 3)
        music_split.setStretchFactor(2, 2)
        self.tabs.addTab(music_split, tool_icon("music"), _("Musik"))

        # --- Hoerbuecher ------------------------------------------------
        self.audiobook_list = QListWidget()
        self.audiobook_list.itemSelectionChanged.connect(self._on_audiobook_selected)

        self.chapter_table = QTableWidget(0, 4)
        self.chapter_table.setHorizontalHeaderLabels(
            [_("Kapitel"), _("Titel"), _("Datei"), _("Status")])
        header = self.chapter_table.horizontalHeader()
        for column in range(4):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
        self.chapter_table.setSortingEnabled(True)
        self.chapter_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.chapter_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.chapter_table.itemSelectionChanged.connect(self._on_chapter_selected)
        self.chapter_table.itemDoubleClicked.connect(lambda _i: self.play_selected())
        self.chapter_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chapter_table.customContextMenuRequested.connect(
            self._chapter_context_menu)

        self.chapter_meta = MetaPanel(self.loader)
        book_split = QSplitter()
        book_split.addWidget(self.audiobook_list)
        book_split.addWidget(self.chapter_table)
        book_split.addWidget(self.chapter_meta)
        book_split.setStretchFactor(0, 1)
        book_split.setStretchFactor(1, 3)
        book_split.setStretchFactor(2, 2)
        self.tabs.addTab(book_split, tool_icon("book"), _("Hoerbuecher"))

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(self.player)
        self.setCentralWidget(central)

    def _build_actions(self) -> None:
        self.actions_map = ActionRegistry(self, _)
        a = self.actions_map
        a.add("add_music_root", "Musik-Ordner …", slot=self._add_music_root)
        a.add("add_audiobook_root", "Hoerbuch-Ordner …",
             slot=self._add_audiobook_root)
        a.add("scan", "Scannen", "F5", self.scan_all, tool_icon("refresh"))
        a.add("auto_match", "Automatisch zuordnen", "Ctrl+T", self.auto_match,
             tool_icon("match"))
        a.add("play", "Abspielen", "Space", self.play_selected, tool_icon("play"),
             target=self.tabs, shortcut_context=Qt.WidgetWithChildrenShortcut)
        a.add("rename", "Umbenennen …", "Ctrl+R", self.rename_preview,
             tool_icon("rename"))
        a.add("save_metadata", "Metadaten in Datei speichern …", "Ctrl+S",
             self.write_metadata_to_file, tool_icon("check"))
        a.add("delete", "Loeschen …", "Del", self.delete_selected,
             tool_icon("delete"), target=self.tabs,
             shortcut_context=Qt.WidgetWithChildrenShortcut)
        a.add("search", "Suchen", "Ctrl+F", self.focus_search)
        a.add("settings", "Einstellungen …", "Ctrl+,", self.open_settings,
             tool_icon("settings"))
        a.add("help", "Hilfe …", "F1", self.open_help, tool_icon("help"))
        a.add("quit", "Beenden", "Ctrl+Q", self.close)

    def _build_toolbar(self) -> None:
        bar = QToolBar()
        bar.setMovable(False)
        bar.setIconSize(QSize(20, 20))
        self.addToolBar(bar)
        a = self.actions_map

        add_action = bar.addAction(tool_icon("folder_new"), _("Ordner hinzufuegen …"))
        menu = QMenu(self)
        menu.addAction(a["add_music_root"])
        menu.addAction(a["add_audiobook_root"])
        add_action.setMenu(menu)
        button = bar.widgetForAction(add_action)
        if isinstance(button, QToolButton):
            button.setPopupMode(QToolButton.InstantPopup)

        bar.addAction(a["scan"])
        bar.addAction(a["auto_match"])
        bar.addSeparator()
        bar.addAction(a["play"])
        bar.addAction(a["rename"])
        bar.addAction(a["delete"])
        bar.addSeparator()
        bar.addAction(a["settings"])
        bar.addAction(a["help"])

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bar.addWidget(spacer)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(_("Suchen …"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMaximumWidth(240)
        self.search_edit.textChanged.connect(self._on_search_changed)
        bar.addWidget(self.search_edit)

    def _build_menubar(self) -> None:
        a = self.actions_map
        bar = self.menuBar()

        menu = bar.addMenu(_("&Datei"))
        menu.addAction(a["add_music_root"])
        menu.addAction(a["add_audiobook_root"])
        menu.addSeparator()
        menu.addAction(a["scan"])
        menu.addSeparator()
        menu.addAction(a["quit"])

        menu = bar.addMenu(_("&Bearbeiten"))
        menu.addAction(a["rename"])
        menu.addAction(a["save_metadata"])
        menu.addAction(a["delete"])

        menu = bar.addMenu(_("&Ansicht"))
        menu.addAction(a["search"])

        menu = bar.addMenu(_("E&xtras"))
        menu.addAction(a["auto_match"])
        menu.addSeparator()
        menu.addAction(a["settings"])

        bar.addMenu(_("&Hilfe")).addAction(a["help"])

    def focus_search(self) -> None:
        self.search_edit.selectAll()
        self.search_edit.setFocus()

    # --- Ordner verwalten -------------------------------------------------
    def _add_music_root(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, _("Ordner waehlen"))
        if not folder:
            return
        self.settings.music_roots.append(folder)
        self.settings.save(self.qsettings)
        self.scan_all()

    def _add_audiobook_root(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, _("Ordner waehlen"))
        if not folder:
            return
        self.settings.audiobook_roots.append(folder)
        self.settings.save(self.qsettings)
        self.scan_all()

    # --- Scannen -----------------------------------------------------
    def scan_all(self) -> None:
        if not self.settings.music_roots and not self.settings.audiobook_roots:
            QMessageBox.information(
                self, _("Scannen"), _("Bitte mindestens einen Ordner hinzufuegen."))
            return

        progress = QProgressDialog(_("Scanne …"), None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.setAutoClose(False)
        progress.setAutoReset(False)

        thread, worker = scanner.run_in_thread(
            self.settings.music_roots, self.settings.audiobook_roots, self.library)
        worker.progress.connect(progress.setLabelText)
        thread.finished.connect(progress.close)
        thread.finished.connect(self.refresh_view)
        thread.finished.connect(
            lambda: self.statusBar().showMessage(_("Scan abgeschlossen."), 4000))
        self._scan_thread, self._scan_worker = thread, worker
        thread.start()
        progress.exec()
        thread.wait(5000)

    def _scan_target(self, folder: Path, root: Path, kind: str) -> None:
        """Nur `folder` neu einlesen - fuer den gezielten Scan eines
        einzelnen Albums oder Hoerbuchs aus dem Kontextmenue, statt jedes
        Mal den ganzen Wurzelordner zu durchsuchen."""
        progress = QProgressDialog(_("Scanne …"), None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.setAutoClose(False)
        progress.setAutoReset(False)

        thread, worker = scanner.run_folder_in_thread(folder, root, kind, self.library)
        worker.progress.connect(progress.setLabelText)
        thread.finished.connect(progress.close)
        thread.finished.connect(self.refresh_view)
        thread.finished.connect(
            lambda: self.statusBar().showMessage(_("Scan abgeschlossen."), 4000))
        self._scan_thread, self._scan_worker = thread, worker
        thread.start()
        progress.exec()
        thread.wait(5000)

    def _scan_track(self, track: Item) -> None:
        root = Path(track.root)
        self._scan_target(subfolder_of(Path(track.path), root), root, TRACK)

    def _scan_chapter(self, chapter: Item) -> None:
        root = Path(chapter.root)
        self._scan_target(subfolder_of(Path(chapter.path), root), root, CHAPTER)

    # --- Ansicht befuellen --------------------------------------------
    def refresh_view(self) -> None:
        self._fill_albums()
        self._fill_tracks()
        self._fill_audiobooks()
        self._fill_chapters()

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text.strip().lower()
        self._fill_tracks()
        self._fill_chapters()

    # --- Musik ---------------------------------------------------------
    def _selected_album(self) -> str | None:
        items = self.album_list.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def _fill_albums(self) -> None:
        selected = {i.data(Qt.UserRole) for i in self.album_list.selectedItems()}
        self.album_list.clear()
        all_item = QListWidgetItem(_("Alle Alben"))
        all_item.setData(Qt.UserRole, None)
        self.album_list.addItem(all_item)
        to_reselect = [all_item] if None in selected or not selected else []
        for name, count in self.library.albums():
            list_item = QListWidgetItem(f"{name}  ({count})")
            list_item.setData(Qt.UserRole, name)
            self.album_list.addItem(list_item)
            if name in selected:
                to_reselect.append(list_item)
        if to_reselect:
            self.album_list.setCurrentItem(to_reselect[0])
            for list_item in to_reselect:
                list_item.setSelected(True)
        elif not selected:
            self.album_list.setCurrentItem(all_item)

    def _on_album_selected(self) -> None:
        self._fill_tracks()

    def _fill_tracks(self) -> None:
        selected_ids = {i.data(Qt.UserRole).id for i in self.track_list.selectedItems()}
        self.track_list.clear()
        album = self._selected_album()
        to_reselect = []
        for item in self.library.list_tracks(album):
            if self._search_text and not (
                    self._search_text in (item.title or "").lower()
                    or self._search_text in (item.artist or "").lower()):
                continue
            list_item = QListWidgetItem(item.title or Path(item.path).stem)
            list_item.setData(Qt.UserRole, item)
            list_item.setData(SUBTITLE_ROLE, item.artist)
            list_item.setData(STATUS_ROLE, item.status)
            list_item.setToolTip(
                f"{item.path}\n{STATUS_LABEL.get(item.status, item.status)}")
            key = item.cover_url or item.path
            pm = self.loader.get(key) if key else None
            if pm and not pm.isNull():
                list_item.setIcon(QIcon(pm))
            self.track_list.addItem(list_item)
            if item.id in selected_ids:
                to_reselect.append(list_item)
        if to_reselect:
            self.track_list.setCurrentItem(to_reselect[0])
            for list_item in to_reselect:
                list_item.setSelected(True)

    def _on_track_selected(self) -> None:
        self.track_meta.show_item(self._current_track())

    # --- Hoerbuecher ------------------------------------------------------
    def _fill_audiobooks(self) -> None:
        selected_titles = {
            i.data(Qt.UserRole) for i in self.audiobook_list.selectedItems()}
        self.audiobook_list.clear()
        self._audiobook_items: dict[str, list[Item]] = {}
        to_reselect = []
        for title, items in self.library.audiobook_groups():
            self._audiobook_items[title] = items
            list_item = QListWidgetItem(f"{title}  ({len(items)})")
            list_item.setData(Qt.UserRole, title)
            self.audiobook_list.addItem(list_item)
            if title in selected_titles:
                to_reselect.append(list_item)
        if to_reselect:
            self.audiobook_list.setCurrentItem(to_reselect[0])
            for list_item in to_reselect:
                list_item.setSelected(True)

    def _on_audiobook_selected(self) -> None:
        self._fill_chapters()

    def _selected_audiobook(self) -> str | None:
        items = self.audiobook_list.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def _fill_chapters(self) -> None:
        title = self._selected_audiobook()
        chapters = sorted(
            self._audiobook_items.get(title, []) if title else [],
            key=lambda e: (e.track_number or 0, e.title))
        if self._search_text:
            chapters = [
                c for c in chapters
                if self._search_text in (c.title or "").lower()
                or self._search_text in (c.book_title or "").lower()]
        self.chapter_table.setSortingEnabled(False)
        self.chapter_table.setRowCount(len(chapters))
        for row, item in enumerate(chapters):
            tag = str(item.track_number) if item.track_number is not None else "?"
            tag_item = QTableWidgetItem(tag)
            tag_item.setData(Qt.UserRole, item)
            self.chapter_table.setItem(row, 0, tag_item)
            self.chapter_table.setItem(row, 1, QTableWidgetItem(item.title))
            file_item = QTableWidgetItem(Path(item.path).name)
            file_item.setToolTip(item.path)
            self.chapter_table.setItem(row, 2, file_item)
            self.chapter_table.setItem(
                row, 3, QTableWidgetItem(STATUS_LABEL.get(item.status, item.status)))
        self.chapter_table.setSortingEnabled(True)
        self.chapter_table.resizeColumnsToContents()

    def _on_chapter_selected(self) -> None:
        self.chapter_meta.show_item(self._current_chapter())

    # --- Auswahl -----------------------------------------------------
    def _selected_tracks(self) -> list[Item]:
        if self.tabs.currentIndex() != 0:
            return []
        return [i.data(Qt.UserRole) for i in self.track_list.selectedItems()]

    def _current_track(self) -> Item | None:
        items = self._selected_tracks()
        return items[0] if items else None

    def _selected_chapters(self) -> list[Item]:
        if self.tabs.currentIndex() != 1:
            return []
        rows = {i.row() for i in self.chapter_table.selectedItems()}
        return [self.chapter_table.item(row, 0).data(Qt.UserRole) for row in rows]

    def _current_chapter(self) -> Item | None:
        rows = self.chapter_table.selectedItems()
        if not rows:
            return None
        return self.chapter_table.item(rows[0].row(), 0).data(Qt.UserRole)

    def _selected_items(self) -> list[Item]:
        return self._selected_tracks() or self._selected_chapters()

    def _on_cover(self, key: str, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        for row in range(self.track_list.count()):
            list_item = self.track_list.item(row)
            item: Item = list_item.data(Qt.UserRole)
            if (item.cover_url or item.path) == key:
                list_item.setIcon(QIcon(pixmap))

    # --- Wiedergabe ------------------------------------------------------
    # --- Automatisches Zuordnen ------------------------------------------
    def auto_match(self) -> None:
        config = self.settings.build_config()
        if not config.providers:
            QMessageBox.warning(
                self, _("Automatisch zuordnen"),
                _("Keine Quelle aktiviert.") + " " + _("Einstellungen …"))
            return
        selected = self._selected_items()
        if selected:
            paths = [Path(i.path) for i in selected]
        else:
            paths = [Path(i.path) for i in self.library.unresolved()]
        if not paths:
            QMessageBox.information(
                self, _("Automatisch zuordnen"),
                _("Nichts zu tun - alles bereits zugeordnet."))
            return

        progress = QProgressDialog(
            _("Ordne zu …"), _("Abbrechen"), 0, len(paths), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)

        thread, worker = matcher.run_in_thread(paths, config, self.library)
        worker.progress.connect(lambda i, n, name: (
            progress.setMaximum(n), progress.setValue(i), progress.setLabelText(name)))
        progress.canceled.connect(worker.stop)
        thread.finished.connect(progress.close)
        thread.finished.connect(self.refresh_view)
        self._match_thread, self._match_worker = thread, worker
        thread.start()
        progress.exec()
        thread.wait(5000)

    def _manual_match(self, item: Item) -> None:
        config = self.settings.build_config()
        dialog = MatchDialog(item, config, self.library, self.loader, self)
        if dialog.exec():
            self.refresh_view()

    def play_selected(self) -> None:
        item = self._current_track() or self._current_chapter()
        if item is None:
            return
        self._play_item(item)

    def _play_item(self, item: Item) -> None:
        path = Path(item.path)
        if not path.exists():
            QMessageBox.warning(
                self, _("Abspielen"),
                _("Datei nicht gefunden - eventuell verschoben oder geloescht."))
            return
        self.player.play(item)

    def _play_next(self) -> None:
        """Naechsten Titel/Kapitel im selben Album/Hoerbuch anspielen, falls
        eines bekannt ist - keine eigene Warteschlange fuer v1."""
        current = self.player.current_item
        if current is None:
            return
        if current.kind == TRACK:
            siblings = self.library.list_tracks(current.album)
        else:
            siblings = sorted(
                self._audiobook_items.get(current.book_title, []),
                key=lambda e: (e.track_number or 0, e.title))
        paths = [Path(i.path) for i in siblings]
        try:
            index = paths.index(Path(current.path))
        except ValueError:
            return
        if index + 1 < len(siblings):
            self._play_item(siblings[index + 1])

    # --- Umbenennen ------------------------------------------------------
    # --- Metadaten in die Datei zurueckschreiben --------------------------
    def write_metadata_to_file(self) -> None:
        """Anders als Umbenennen/Loeschen aendert das die Originaldatei
        selbst - deshalb ausdruecklich bestaetigen lassen und nie
        automatisch beim Scannen/Zuordnen aufrufen."""
        items = self._selected_items()
        if not items:
            QMessageBox.information(
                self, _("Metadaten speichern …"),
                _("Bitte mindestens eine Datei waehlen."))
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(_("Metadaten speichern …"))
        box.setText(
            _("Metadaten von {n} Datei(en) direkt in die Datei schreiben?")
            .format(n=len(items)))
        box.setInformativeText(_("Das aendert die Originaldatei."))
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Cancel)
        if box.exec() != QMessageBox.Yes:
            return

        errors: list[str] = []
        for item in items:
            path = Path(item.path)
            tags = TrackTags(
                title=item.title, artist=item.artist, album=item.album,
                album_artist=item.album_artist, track_number=item.track_number,
                year=item.year, genre=item.genre)
            try:
                write_track_tags(path, tags)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path.name}: {exc}")
        if errors:
            QMessageBox.warning(
                self, _("Metadaten speichern …"),
                _("Nicht alles konnte gespeichert werden:") + "\n"
                + "\n".join(errors))
        else:
            QMessageBox.information(
                self, _("Metadaten speichern …"), _("Metadaten gespeichert."))

    def rename_preview(self) -> None:
        items = self._selected_items()
        if not items:
            items = self.library.all_items()
        ops = renamer.build_plan(
            items, self.settings.track_template, self.settings.chapter_template)
        unchanged = sum(1 for op in ops if op.status == "same")
        pending = [op for op in ops if op.status != "same"]
        if not pending:
            QMessageBox.information(
                self, _("Umbenennen …"),
                _("Nichts zu tun - alle Dateien bereits korrekt benannt."))
            return
        dialog = RenameDialog(pending, self.library, unchanged, self)
        if dialog.exec():
            self.refresh_view()

    # --- Loeschen --------------------------------------------------------
    def delete_selected(self) -> None:
        items = self._selected_items()
        if not items:
            QMessageBox.information(
                self, _("Loeschen …"), _("Bitte mindestens eine Datei waehlen."))
            return
        names = "\n".join(f"- {Path(i.path).name}" for i in items[:10])
        if len(items) > 10:
            names += f"\n… (+{len(items) - 10})"
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(_("Loeschen …"))
        box.setText(
            _("{n} Datei(en) in den Papierkorb verschieben?").format(n=len(items)))
        box.setInformativeText(names)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Cancel)
        if box.exec() != QMessageBox.Yes:
            return
        errors: list[str] = []
        for item in items:
            path = Path(item.path)
            try:
                send2trash(str(path))
                self.library.remove_path(path)
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")
        self.refresh_view()
        if errors:
            QMessageBox.warning(
                self, _("Loeschen …"),
                _("Nicht alles konnte geloescht werden:") + "\n" + "\n".join(errors))

    # --- Kontextmenues -------------------------------------------------
    def _track_context_menu(self, pos) -> None:
        items = self._selected_tracks()
        if not items:
            return
        menu = QMenu(self)
        menu.addAction(self.actions_map["play"])
        menu.addSeparator()
        menu.addAction(self.actions_map["auto_match"])
        if len(items) == 1:
            menu.addAction(_("Manuell zuordnen …"),
                           lambda: self._manual_match(items[0]))
            menu.addAction(
                tool_icon("refresh"), _("Nur dieses Album scannen"),
                # Erst starten, wenn das Kontextmenue sich geschlossen hat -
                # ein QThread + modaler Dialog waehrend dessen eigener
                # Event-Schleife (Popup-Grab) kann sonst abstuerzen.
                lambda: QTimer.singleShot(0, lambda: self._scan_track(items[0])))
        menu.addSeparator()
        menu.addAction(self.actions_map["rename"])
        menu.addAction(self.actions_map["save_metadata"])
        menu.addSeparator()
        menu.addAction(self.actions_map["delete"])
        menu.exec(self.track_list.viewport().mapToGlobal(pos))

    def _chapter_context_menu(self, pos) -> None:
        items = self._selected_chapters()
        if not items:
            return
        menu = QMenu(self)
        menu.addAction(self.actions_map["play"])
        menu.addSeparator()
        menu.addAction(self.actions_map["auto_match"])
        if len(items) == 1:
            menu.addAction(_("Manuell zuordnen …"),
                           lambda: self._manual_match(items[0]))
            menu.addAction(
                tool_icon("refresh"), _("Nur dieses Hoerbuch scannen"),
                # Erst starten, wenn das Kontextmenue sich geschlossen hat -
                # ein QThread + modaler Dialog waehrend dessen eigener
                # Event-Schleife (Popup-Grab) kann sonst abstuerzen.
                lambda: QTimer.singleShot(0, lambda: self._scan_chapter(items[0])))
        menu.addSeparator()
        menu.addAction(self.actions_map["rename"])
        menu.addAction(self.actions_map["save_metadata"])
        menu.addSeparator()
        menu.addAction(self.actions_map["delete"])
        menu.exec(self.chapter_table.viewport().mapToGlobal(pos))

    # --- Einstellungen/Hilfe --------------------------------------------
    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() and dialog.result_settings:
            self.settings = dialog.result_settings
            self.settings.save(self.qsettings)
            set_language(self.settings.language)
            self.refresh_view()

    def open_help(self) -> None:
        HelpDialog(self).exec()

    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802
        self.player.stop()
        for attr in ("_scan_thread", "_match_thread"):
            thread = getattr(self, attr, None)
            if thread is not None and thread.isRunning():
                thread.wait(2000)
        self.library.close()
        super().closeEvent(event)
