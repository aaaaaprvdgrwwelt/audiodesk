"""Einstellungen, gehalten in QSettings."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from PySide6.QtCore import QSettings

from deskkit.secrets import get_secret, set_secret
from deskkit.settings import as_bool as _bool

from .matcher import DEFAULT_THRESHOLD, MatchConfig
from .providers.base import MetadataProvider
from .providers.discogs import DiscogsProvider
from .providers.itunes_audiobooks import ItunesAudiobooksProvider
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
    #: iTunes Search API - einzige eingebaute Hoerbuch-Quelle, kein Key
    #: noetig, deshalb per Vorgabe an.
    use_itunes_audiobooks: bool = True
    threshold: int = DEFAULT_THRESHOLD
    track_template: str = TRACK_TEMPLATE_DEFAULT
    chapter_template: str = CHAPTER_TEMPLATE_DEFAULT
    language: str = "auto"
    #: Lautstaerke der Wiedergabeleiste (0-100) - bleibt sonst bei jedem
    #: Neustart auf dem QAudioOutput-Vorgabewert stehen.
    volume: int = 80

    @classmethod
    def load(cls, settings: QSettings) -> Settings:
        settings.beginGroup("audiodesk")
        obj = cls(
            music_roots=json.loads(settings.value("music_roots", "[]") or "[]"),
            audiobook_roots=json.loads(
                settings.value("audiobook_roots", "[]") or "[]"),
            use_musicbrainz=_bool(settings.value("use_musicbrainz"), True),
            discogs_token=get_secret(settings, "audiodesk", "discogs_token"),
            use_discogs=_bool(settings.value("use_discogs"), False),
            lastfm_key=get_secret(settings, "audiodesk", "lastfm_key"),
            use_lastfm=_bool(settings.value("use_lastfm"), False),
            use_itunes_audiobooks=_bool(
                settings.value("use_itunes_audiobooks"), True),
            threshold=int(settings.value("threshold", DEFAULT_THRESHOLD)),
            track_template=settings.value(
                "track_template", TRACK_TEMPLATE_DEFAULT) or TRACK_TEMPLATE_DEFAULT,
            chapter_template=settings.value(
                "chapter_template", CHAPTER_TEMPLATE_DEFAULT)
            or CHAPTER_TEMPLATE_DEFAULT,
            language=settings.value("language", "auto") or "auto",
            volume=int(settings.value("volume", 80)),
        )
        settings.endGroup()
        return obj

    #: Landen im System-Schluesselbund statt im Klartext in QSettings
    #: (siehe deskkit.secrets).
    _SECRET_FIELDS = ("discogs_token", "lastfm_key")

    def save(self, settings: QSettings) -> None:
        settings.beginGroup("audiodesk")
        for key, value in self.__dict__.items():
            if key in self._SECRET_FIELDS:
                set_secret(settings, "audiodesk", key, value)
                continue
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
        if self.use_itunes_audiobooks:
            providers.append(ItunesAudiobooksProvider())
        return providers

    def build_config(self) -> MatchConfig:
        return MatchConfig(threshold=self.threshold, providers=self.build_providers())
