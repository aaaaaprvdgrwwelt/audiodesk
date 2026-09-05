"""Einstellungen, gehalten in QSettings."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from PySide6.QtCore import QSettings

from deskkit.settings import as_bool as _bool

from .matcher import DEFAULT_THRESHOLD, MatchConfig
from .providers.base import MetadataProvider
from .providers.discogs import DiscogsProvider
from .providers.lastfm import LastFmProvider
from .providers.musicbrainz import MusicBrainzProvider

TRACK_TEMPLATE_DEFAULT = "{artist}/{album}/{track_number:02} - {title}{ext}"
CHAPTER_TEMPLATE_DEFAULT = "{book_title}/{chapter:03} - {title}{ext}"


@dataclass
class Settings:
    #: Getrennte Wurzeln wie bei moviedesk (movie_roots/series_roots) -
    #: zuverlaessiger als der Versuch, Musik automatisch von Hoerbuechern
    #: zu unterscheiden.
    music_roots: list[str] = field(default_factory=list)
    audiobook_roots: list[str] = field(default_factory=list)
    use_musicbrainz: bool = True
    discogs_token: str = ""
    use_discogs: bool = False
    lastfm_key: str = ""
    use_lastfm: bool = False
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
            discogs_token=settings.value("discogs_token", "") or "",
            use_discogs=_bool(settings.value("use_discogs"), False),
            lastfm_key=settings.value("lastfm_key", "") or "",
            use_lastfm=_bool(settings.value("use_lastfm"), False),
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

    # ------------------------------------------------------------------
    def build_providers(self) -> list[MetadataProvider]:
        providers: list[MetadataProvider] = []
        if self.use_musicbrainz:
            providers.append(MusicBrainzProvider())
        if self.use_discogs and self.discogs_token.strip():
            providers.append(DiscogsProvider(self.discogs_token))
        if self.use_lastfm and self.lastfm_key.strip():
            providers.append(LastFmProvider(self.lastfm_key))
        return providers

    def build_config(self) -> MatchConfig:
        return MatchConfig(threshold=self.threshold, providers=self.build_providers())
