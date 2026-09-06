# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).
Noch kein Release getaggt — alles bislang unter „Unreleased“.

## [Unreleased]

### Added

- Musik- (Album/Track) und Hörbuch-Bibliothek (Buch/Kapitel) in einer
  gemeinsamen Datenbank, mit dauerhafter Wiedergabeleiste statt
  Reader-Fenster pro Datei.
- Tags lesen/schreiben über mutagen (MP3/ID3, MP4/M4B, FLAC, OGG),
  Metadaten in die Originaldatei zurückschreiben (`Strg+S`).
- Metadaten-Abgleich gegen MusicBrainz, Discogs und Last.fm (Musik) sowie
  Apples iTunes Search API (einzige eingebaute Hörbuch-Quelle).
- Discogs-Interpret/-Titel über den Release-Detailaufruf statt nur der
  ungenauen Heuristik aus dem Suchtreffer.
- M4B-Kapitelmarken auslesen und in der Wiedergabeleiste als Sprungliste
  anspringbar machen.
- Warteschlange, Zufallswiedergabe und Wiederholen (aus/alle/aktueller
  Titel).
- Lautstärke wird über einen Neustart hinweg gemerkt.
- Gezielter Scan nur eines einzelnen Albums/Hörbuchs statt des ganzen
  Wurzelordners.
- Windows-Installer und macOS-Pakete (PyInstaller + Inno Setup), gebaut in
  CI bei einem Versions-Tag.
- `.desktop`-Eintrag für Quellinstallationen unter Linux.
- Scan-Fortschrittsdialog mit „Abbrechen“-Knopf.
- Testsuite (pytest) für Tags, Matcher, Bibliotheksindex, Scanner,
  Discogs-Provider, Kapitelmarken, Wiedergabe-Warteschlange.
- CI (GitHub Actions): Tests bei jedem Push/PR.
- Projektseite unter `aaaaaprvdgrwwelt.github.io/audiodesk`.

### Changed

- Gemeinsame Bausteine (Kachel-Delegate, Ordnerliste) nach
  [deskkit](https://github.com/aaaaaprvdgrwwelt/deskkit) ausgelagert —
  geteilt mit MovieDesk, ComicDesk und BookDesk.

### Security

- Discogs-Token und Last.fm-Key landen im System-Schlüsselbund statt im
  Klartext in der Konfigurationsdatei.

[Unreleased]: https://github.com/aaaaaprvdgrwwelt/audiodesk/commits/main
