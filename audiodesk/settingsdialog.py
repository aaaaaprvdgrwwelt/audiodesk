"""Quellen, Schwellwert, Umbenennen-Vorlagen und Bibliotheksordner."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QSlider, QTabWidget, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from deskkit.widgets import RootList

from .config import Settings
from .i18n import LANGUAGES, _


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
        self.music_roots = RootList(settings.music_roots, _)
        layout.addWidget(self.music_roots)
        layout.addWidget(QLabel(_("Hoerbuch-Ordner")))
        self.audiobook_roots = RootList(settings.audiobook_roots, _)
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

        itunes_box = QGroupBox(_("iTunes (Hoerbuecher)"))
        self.use_itunes_audiobooks = QCheckBox(_("Aktiv (kein API-Key noetig)"))
        self.use_itunes_audiobooks.setChecked(settings.use_itunes_audiobooks)
        form = QFormLayout(itunes_box)
        form.addRow(self.use_itunes_audiobooks)
        itunes_hint = QLabel(_(
            "Einzige eingebaute Hoerbuch-Quelle - MusicBrainz/Discogs/"
            "Last.fm sind reine Musikdatenbanken und werden fuer Hoerbuecher "
            "nicht befragt."))
        itunes_hint.setWordWrap(True)
        form.addRow(itunes_hint)

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
        layout.addWidget(itunes_box)
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
            use_itunes_audiobooks=self.use_itunes_audiobooks.isChecked(),
            threshold=self.threshold.value(),
            track_template=self.track_template.text().strip(),
            chapter_template=self.chapter_template.text().strip(),
            language=self.language.currentData(),
        )
        self.accept()
