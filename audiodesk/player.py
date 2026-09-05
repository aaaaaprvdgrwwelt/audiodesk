"""Wiedergabe: eine dauerhafte Leiste im Hauptfenster statt eines
Reader-Fensters pro Datei - bei Audio das uebliche Bedienmuster
(Winamp/iTunes/Spotify-Stil)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

from .i18n import _
from .icons import icon as tool_icon
from .library import Item, LibraryIndex

#: Wie oft der Fortschritt in der Bibliothek gesichert wird - bei einem
#: Hoerbuch macht das den Fortschritt persistent, bei Musik ist es harmlos
#: ungenutzt.
SAVE_INTERVAL_MS = 2000


def format_ms(ms: int) -> str:
    seconds = max(ms, 0) // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


class PlayerBar(QWidget):
    """`finished` feuert, wenn ein Stueck zu Ende gespielt hat - der
    Aufrufer entscheidet, ob/was als naechstes kommt."""

    finished = Signal()

    def __init__(self, library: LibraryIndex, parent=None):
        super().__init__(parent)
        self.library = library
        self.current_item: Item | None = None
        self.current_path: Path | None = None
        self._seeking = False

        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._output.setVolume(0.8)
        self._player.setAudioOutput(self._output)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)

        self.play_button = QPushButton()
        self.play_button.setIcon(tool_icon("play"))
        self.play_button.setEnabled(False)
        self.play_button.setToolTip(_("Wiedergabe/Pause"))
        self.play_button.clicked.connect(self.toggle)

        self.title_label = QLabel(_("Keine Wiedergabe"))
        self.title_label.setMinimumWidth(180)

        self.position_label = QLabel("0:00")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self._seek_preview)
        self.slider.sliderReleased.connect(self._seek_commit)
        self.duration_label = QLabel("0:00")

        volume_label = QLabel()
        volume_label.setPixmap(tool_icon("volume").pixmap(16, 16))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setMaximumWidth(90)
        self.volume_slider.valueChanged.connect(
            lambda v: self._output.setVolume(v / 100))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self.play_button)
        layout.addWidget(self.title_label)
        layout.addWidget(self.position_label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.duration_label)
        layout.addWidget(volume_label)
        layout.addWidget(self.volume_slider)

        self._save_timer = QTimer(self)
        self._save_timer.setInterval(SAVE_INTERVAL_MS)
        self._save_timer.timeout.connect(self._save_position)

    # ------------------------------------------------------------------
    def play(self, item: Item, start_ms: int | None = None) -> None:
        self.current_item = item
        self.current_path = Path(item.path)
        self._player.setSource(QUrl.fromLocalFile(str(self.current_path)))
        self._player.setPosition(
            start_ms if start_ms is not None else (item.last_position_ms or 0))
        self._player.play()
        self.title_label.setText(item.title or self.current_path.name)
        self.play_button.setEnabled(True)
        self._save_timer.start()

    def toggle(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self) -> None:
        self._save_position()
        self._player.stop()
        self._save_timer.stop()

    def is_playing(self, path: Path) -> bool:
        return (self.current_path == path
                and self._player.playbackState() == QMediaPlayer.PlayingState)

    # --- Player-Signale --------------------------------------------------
    def _on_state_changed(self, state) -> None:
        icon_name = "pause" if state == QMediaPlayer.PlayingState else "play"
        self.play_button.setIcon(tool_icon(icon_name))

    def _on_duration_changed(self, duration: int) -> None:
        self.slider.setRange(0, duration)
        self.duration_label.setText(format_ms(duration))

    def _on_position_changed(self, position: int) -> None:
        if not self._seeking:
            self.slider.setValue(position)
        self.position_label.setText(format_ms(position))

    def _on_media_status(self, status) -> None:
        if status == QMediaPlayer.EndOfMedia:
            self._save_timer.stop()
            if self.current_path is not None:
                self.library.set_last_position_ms(self.current_path, 0)
            self.finished.emit()

    def _on_error(self, error, error_string: str) -> None:
        if error != QMediaPlayer.NoError:
            self.title_label.setText(_("Wiedergabe fehlgeschlagen: {error}")
                                     .format(error=error_string))

    # --- Bedienung ---------------------------------------------------
    def _seek_preview(self, value: int) -> None:
        self._seeking = True
        self.position_label.setText(format_ms(value))

    def _seek_commit(self) -> None:
        self._player.setPosition(self.slider.value())
        self._seeking = False

    def _save_position(self) -> None:
        if self.current_path is not None:
            self.library.set_last_position_ms(
                self.current_path, self._player.position())
