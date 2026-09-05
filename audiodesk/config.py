"""Einstellungen, gehalten in QSettings."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from PySide6.QtCore import QSettings

from deskkit.settings import as_bool as _bool

TRACK_TEMPLATE_DEFAULT = "{artist}/{album}/{track_number:02} - {title}{ext}"
CHAPTER_TEMPLATE_DEFAULT = "{book_title}/{chapter:03} - {title}{ext}"
DEFAULT_THRESHOLD = 70


@dataclass
class Settings:
    #: Getrennte Wurzeln wie bei moviedesk (movie_roots/series_roots) -
    #: zuverlaessiger als der Versuch, Musik automatisch von Hoerbuechern
    #: zu unterscheiden.
    music_roots: list[str] = field(default_factory=list)
    audiobook_roots: list[str] = field(default_factory=list)
    use_musicbrainz: bool = True
    threshold: int = DEFAULT_THRESHOLD
    track_template: str = TRACK_TEMPLATE_DEFAULT
    chapter_template: str = CHAPTER_TEMPLATE_DEFAULT
    language: str = "auto"

    @classmethod
    def load(cls, settings: QSettings) -> "Settings":
        settings.beginGroup("audiodesk")
        obj = cls(
            music_roots=json.loads(settings.value("music_roots", "[]") or "[]"),
            audiobook_roots=json.loads(
                settings.value("audiobook_roots", "[]") or "[]"),
            use_musicbrainz=_bool(settings.value("use_musicbrainz"), True),
            threshold=int(settings.value("threshold", DEFAULT_THRESHOLD)),
            track_template=settings.value(
                "track_template", TRACK_TEMPLATE_DEFAULT) or TRACK_TEMPLATE_DEFAULT,
            chapter_template=settings.value(
                "chapter_template", CHAPTER_TEMPLATE_DEFAULT)
            or CHAPTER_TEMPLATE_DEFAULT,
            language=settings.value("language", "auto") or "auto",
        )
        settings.endGroup()
        return obj

    def save(self, settings: QSettings) -> None:
        settings.beginGroup("audiodesk")
        for key, value in self.__dict__.items():
            if isinstance(value, list):
                value = json.dumps(value)
            settings.setValue(key, value)
        settings.endGroup()
        settings.sync()
