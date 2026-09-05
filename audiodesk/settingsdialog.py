"""Quellen, Schwellwert, Umbenennen-Vorlagen und Bibliotheksordner."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton,
    QSlider, QTabWidget, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from .config import Settings
from .i18n import LANGUAGES, _


class _RootList(QWidget):
    """Ordnerliste mit Hinzufuegen/Entfernen - fuer Musik- oder
    Hoerbuch-Wurzeln."""

    def __init__(self, roots: list[str], parent=None):
        super().__init__(parent)
        self.list = QListWidget()
        self.list.addItems(roots)

        add_button = QPushButton(_("Ordner hinzufuegen …"))
        add_button.clicked.connect(self._add)
        remove_button = QPushButton(_("Entfernen"))
        remove_button.clicked.connect(self._remove)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(remove_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

    def _add(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, _("Ordner waehlen"))
        if folder:
            self.list.addItem(folder)

    def _remove(self) -> None:
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def roots(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Einstellungen …"))
        self.resize(560, 480)
        self.result_settings: Settings | None = None

        tabs = QTabWidget()
        tabs.addTab(self._library_tab(settings), _("Bibliothek"))
        tabs.addTab(self._sources_tab(settings), _("Quellen"))
        tabs.addTab(self._rename_tab(settings), _("Umbenennen"))
        tabs.addTab(self._general_tab(settings), _("Allgemein"))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    def _library_tab(self, settings: Settings) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(_("Musik-Ordner")))
        self.music_roots = _RootList(settings.music_roots)
        layout.addWidget(self.music_roots)
        layout.addWidget(QLabel(_("Hoerbuch-Ordner")))
        self.audiobook_roots = _RootList(settings.audiobook_roots)
        layout.addWidget(self.audiobook_roots)
        return widget

    def _sources_tab(self, settings: Settings) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        mb_box = QGroupBox("MusicBrainz")
        self.use_musicbrainz = QCheckBox(_("Aktiv (kein API-Key noetig)"))
        self.use_musicbrainz.setChecked(settings.use_musicbrainz)
        form = QFormLayout(mb_box)
        form.addRow(self.use_musicbrainz)

        discogs_box = QGroupBox("Discogs")
        self.use_discogs = QCheckBox(_("Aktiv"))
        self.use_discogs.setChecked(settings.use_discogs)
        self.discogs_token = QLineEdit(settings.discogs_token)
        form = QFormLayout(discogs_box)
        form.addRow(self.use_discogs)
        form.addRow(_("Zugriffs-Token"), self.discogs_token)

        lastfm_box = QGroupBox("Last.fm")
        self.use_lastfm = QCheckBox(_("Aktiv"))
        self.use_lastfm.setChecked(settings.use_lastfm)
        self.lastfm_key = QLineEdit(settings.lastfm_key)
        form = QFormLayout(lastfm_box)
        form.addRow(self.use_lastfm)
        form.addRow(_("API-Key"), self.lastfm_key)

        threshold_box = QGroupBox(_("Schwellwert fuer automatische Zuordnung"))
        self.threshold = QSlider(Qt.Horizontal)
        self.threshold.setRange(0, 100)
        self.threshold.setValue(settings.threshold)
        self.threshold_label = QLabel(str(settings.threshold))
        self.threshold.valueChanged.connect(
            lambda v: self.threshold_label.setText(str(v)))
        row = QHBoxLayout(threshold_box)
        row.addWidget(self.threshold, 1)
        row.addWidget(self.threshold_label)

        layout.addWidget(mb_box)
        layout.addWidget(discogs_box)
        layout.addWidget(lastfm_box)
        layout.addWidget(threshold_box)
        layout.addStretch(1)
        return widget

    def _rename_tab(self, settings: Settings) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(
            _("Platzhalter Musik: {artist} {album} {track_number} {title} {year} {ext}")))
        self.track_template = QLineEdit(settings.track_template)
        layout.addWidget(self.track_template)

        layout.addWidget(QLabel(
            _("Platzhalter Hoerbuecher: {book_title} {chapter} {title} {ext}")))
        self.chapter_template = QLineEdit(settings.chapter_template)
        layout.addWidget(self.chapter_template)
        layout.addStretch(1)
        return widget

    def _general_tab(self, settings: Settings) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.language = QComboBox()
        for code, label in LANGUAGES.items():
            self.language.addItem(label, code)
        index = self.language.findData(settings.language)
        if index >= 0:
            self.language.setCurrentIndex(index)
        form.addRow(_("Sprache"), self.language)
        return widget

    # ------------------------------------------------------------------
    def _accept(self) -> None:
        self.result_settings = Settings(
            music_roots=self.music_roots.roots(),
            audiobook_roots=self.audiobook_roots.roots(),
            use_musicbrainz=self.use_musicbrainz.isChecked(),
            discogs_token=self.discogs_token.text().strip(),
            use_discogs=self.use_discogs.isChecked(),
            lastfm_key=self.lastfm_key.text().strip(),
            use_lastfm=self.use_lastfm.isChecked(),
            threshold=self.threshold.value(),
            track_template=self.track_template.text().strip(),
            chapter_template=self.chapter_template.text().strip(),
            language=self.language.currentData(),
        )
        self.accept()
