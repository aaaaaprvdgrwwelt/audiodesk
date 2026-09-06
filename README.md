# AudioDesk

[![Tests](https://github.com/aaaaaprvdgrwwelt/audiodesk/actions/workflows/tests.yml/badge.svg)](https://github.com/aaaaaprvdgrwwelt/audiodesk/actions/workflows/tests.yml)

Ein Dateimanager, der nur Audio kennt: Musik und Hörbücher sichten, hören,
Metadaten holen, umbenennen, löschen. Python + Qt (PySide6), auf demselben
[deskkit](https://github.com/aaaaaprvdgrwwelt/deskkit)-Fundament wie
[MovieDesk](https://github.com/aaaaaprvdgrwwelt/moviedesk),
[ComicDesk](https://github.com/aaaaaprvdgrwwelt/comicdesk) und
[BookDesk](https://github.com/aaaaaprvdgrwwelt/bookdesk). Läuft unter
Linux, Windows und macOS. Oberfläche auf Deutsch und Englisch.

Musik (Album/Track) und Hörbücher (Buch/Kapitel) leben in einer
gemeinsamen Bibliothek, mit einer dauerhaften Wiedergabeleiste statt einem
Reader-Fenster — Warteschlange, Zufallswiedergabe und Wiederholen
inklusive. Metadaten kommen zuerst aus den eingebetteten Tags (MP3/ID3,
MP4/M4B, FLAC, OGG — über [mutagen](https://mutagen.readthedocs.io/)),
ergänzt durch einen optionalen Abgleich gegen bis zu vier Online-Quellen.

> Status: nutzbar. Entwickelt und getestet unter Linux; Windows und macOS
> sollten funktionieren (reines Qt/Python), sind aber nicht manuell
> getestet — siehe [Bekannte Grenzen](#bekannte-grenzen).

## Installation

### Fertige Pakete (Windows, macOS)

Unter [Releases](https://github.com/aaaaaprvdgrwwelt/audiodesk/releases)
liegen ein Windows-Installer und je ein DMG für Apple Silicon und Intel.
Python muss dafür nicht installiert sein.

Beide sind **nicht signiert** — ein Zertifikat kostet mehr, als ein
kostenloses Projekt ausgeben mag. Deshalb einmalig:

* **Windows:** „Der Computer wurde geschützt“ → *Weitere Informationen* →
  *Trotzdem ausführen*.
* **macOS:** beim ersten Start *Rechtsklick auf AudioDesk → Öffnen*, dann
  im Dialog *Öffnen*. Ein Doppelklick allein wird abgelehnt.

Wie die Pakete entstehen, steht in [packaging/](packaging/README.md).

### Aus dem Quelltext (Linux und alle anderen)

Voraussetzung ist Python 3.10 oder neuer. `deskkit` muss als
Geschwister-Ordner neben `audiodesk/` liegen (siehe `requirements.txt`,
`-e ../deskkit`):

```bash
git clone https://github.com/aaaaaprvdgrwwelt/deskkit.git
git clone https://github.com/aaaaaprvdgrwwelt/audiodesk.git
cd audiodesk
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Unter Linux zusätzlich `libpulse0` (oder die entsprechende
PulseAudio-Client-Bibliothek der Distribution) für die Wiedergabe über
`QtMultimedia`.

## Starten

```bash
./audiodesk.sh                 # oder: .venv/bin/python -m audiodesk
./install-desktop.sh           # Eintrag im Anwendungsmenue und Symbole anlegen (Linux)
```

Unter Windows/macOS entsprechend `.venv\Scripts\python -m audiodesk` bzw.
`.venv/bin/python -m audiodesk`.

## Erste Schritte

1. Über **Ordner hinzufügen …** einen Musik- und/oder Hörbuch-Ordner
   angeben — beide werden getrennt geführt, damit Musik nicht
   versehentlich als Hörbuch-Kapitel landet und umgekehrt.
2. **Scannen** (`F5`) liest die Ordner ein — Titel/Interpret/Album/Cover
   kommen aus den eingebetteten Tags.
3. **Automatisch zuordnen** (`Strg+T`) ergänzt fehlende Angaben und ein
   Cover über eine der Online-Quellen (siehe unten). Unsichere oder
   fehlgeschlagene Treffer bleiben markiert und lassen sich per
   Rechtsklick → *Manuell zuordnen* nachtragen.
4. Doppelklick oder **Abspielen** (`Leertaste`) startet die
   Wiedergabeleiste am unteren Fensterrand.

## Metadaten-Quellen

Alle vier Quellen sind optional und einzeln unter *Einstellungen →
Quellen* ein-/ausschaltbar. **MusicBrainz**, **Discogs** und **Last.fm**
sind reine Musikdatenbanken und werden für Hörbuch-Kapitel gar nicht erst
befragt — dafür gibt es die eigene iTunes-Hörbuch-Quelle. API-Keys landen
im System-Schlüsselbund statt im Klartext, siehe
[deskkit](https://github.com/aaaaaprvdgrwwelt/deskkit#readme).

| Quelle | Für | Key nötig? | Anmerkung |
|---|---|---|---|
| **MusicBrainz** | Musik | Nein | Empfohlen, per Vorgabe aktiv. Titel, Interpret, Album, Cover über das Cover Art Archive. |
| **Discogs** | Musik | Ja, kostenlos ([discogs.com/settings/developers](https://www.discogs.com/settings/developers), persönlicher Zugriffs-Token, kein OAuth) | Zweitquelle. Interpret/Titel kommen über den Release-Detailaufruf sauber getrennt (nicht nur aus dem kombinierten Suchtreffertitel geraten). |
| **Last.fm** | Musik | Ja, kostenlos ([last.fm/api/account/create](https://www.last.fm/api/account/create)) | Zweitquelle. |
| **iTunes** | Hörbücher | Nein | Einzige eingebaute Hörbuch-Quelle, per Vorgabe aktiv. Apples öffentliche Suche kennt eine Hörbuch-Kategorie und liefert Titel, Autor (als „Interpret“) und Cover. Abdeckung ist nicht vollständig. |

**Bewusst nicht eingebaut: Audible.** Audible bietet keine öffentliche
API an, ein Zugriff liefe nur über Scraping der Webseite gegen deren
Nutzungsbedingungen — das macht AudioDesk nicht, auch nicht über
importierte Skripte anderer Tools.

## Wiedergabe

Eine dauerhafte Leiste am unteren Fensterrand statt eines Dialogs pro
Datei — das übliche Bedienmuster für Audio.

* **Warteschlange** — eigener Tab, per Rechtsklick auf Titel/Kapitel →
  *Zur Warteschlange hinzufügen* / *Als nächstes abspielen* befüllt, per
  Ziehen umsortierbar, per Kontextmenü entfernbar/leerbar. Hat Vorrang vor
  allem Folgenden.
* **Zufallswiedergabe** — Knopf in der Leiste; wählt beim Weiterspielen
  einen zufälligen anderen Titel aus demselben Album/Hörbuch statt der
  Reihe nach vorzugehen.
* **Wiederholen** — Knopf, schaltet zwischen *aus*, *alle* (springt am
  Ende zurück zum ersten Titel) und *aktueller Titel* durch.
* **Kapitelmarken bei M4B** — eingebettete Nero-Kapitelmarken
  (`chpl`-Atom, wie sie z. B. `m4b-tool` oder ffmpeg schreiben) werden
  ausgelesen und erscheinen als Sprungliste neben dem Titel; ohne solche
  Marken läuft die Datei als ein durchgehendes Stück.
* **Lautstärke** wird über Neustarts hinweg gemerkt.
* Bei Hörbüchern wird die Wiedergabeposition laufend gesichert.

## Musik-Ordner vs. Hörbuch-Ordner

Beide Ordnerarten werden getrennt in den Einstellungen gepflegt. Eine
automatische Erkennung anhand der Datei allein wäre unzuverlässig —
deshalb legt der Ordner fest, ob eine Datei als Musikstück (zu einem
Album gruppiert) oder als Hörbuch-Kapitel (zu einem Hörbuch gruppiert,
meist über den Album-Tag oder sonst den Ordnernamen) geführt wird.

## Nur ein einzelnes Album/Hörbuch neu scannen

Rechtsklick auf einen Titel → *Nur dieses Album scannen*, bzw. auf ein
Kapitel → *Nur dieses Hörbuch scannen*. Anders als bei BookDesk gibt es
hier eine echte Ordnerkonvention pro Album/Hörbuch (siehe
Umbenennen-Vorlagen unten), ein gezielter Scan des einen Ordners ist also
zuverlässig möglich — wie bei MovieDesks „Nur diesen Film/diese Serie
scannen“.

## Umbenennen …

`Strg+R`, Vorschau vor jeder Änderung. Vorlagen frei einstellbar unter
*Einstellungen → Umbenennen*, getrennt für Musik und Hörbücher, Vorgabe:

* Musik: `{artist}/{album}/{track_number:02} - {title}{ext}`
* Hörbücher: `{book_title}/{chapter:03} - {title}{ext}`

Ein `/` in der Vorlage legt eine neue Ordnerebene an.

## Löschen

Verschiebt Dateien in den Papierkorb, nichts wird endgültig gelöscht.

## Bedienung

| Kürzel | Aktion |
|---|---|
| `F5` | Scannen |
| `Strg+T` | Automatisch zuordnen |
| `Leertaste` | Abspielen |
| `Strg+R` | Umbenennen … |
| `Strg+S` | Metadaten in Datei speichern … |
| `Strg+F` | Suchen |
| `Entf` | Löschen … |
| `Strg+,` | Einstellungen … |
| `F1` | Hilfe … |
| `Strg+Q` | Beenden |

## Wo Daten liegen

| Was | Wo |
|---|---|
| Einstellungen | `~/.config/audiodesk/audiodesk.conf` |
| API-Keys | System-Schlüsselbund (Fallback: Klartext in obiger Datei) |
| Bibliotheksindex (Zuordnungen, Wiedergabefortschritt) | `~/.local/share/audiodesk/library.sqlite` |
| Antwort-Cache, Cover | `~/.cache/audiodesk/` |

## Aufbau

- `audiodesk/tags.py` — Tags lesen/schreiben (mutagen, formatübergreifend),
  Cover-Extraktion je Formattyp, M4B-Kapitelmarken
- `audiodesk/scanner.py` — Ordner einlesen (voller Scan über Musik-/
  Hörbuch-Ordner und gezielter Scan eines einzelnen Albums/Hörbuchs),
  beides abbrechbar
- `audiodesk/library.py` — SQLite-Bibliotheksindex, TRACK/CHAPTER-Kinds,
  Gruppierung nach Album/Hörbuchtitel (case-insensitiv)
- `audiodesk/matcher.py` — Kandidaten sammeln und bewerten (Titel,
  Interpret, Album), Quellen-Weiche über `supports_track`/`supports_chapter`
- `audiodesk/providers/` — `musicbrainz.py`, `discogs.py`, `lastfm.py`,
  `itunes_audiobooks.py` hinter einer gemeinsamen Schnittstelle (`base.py`)
- `audiodesk/player.py` — `PlayerBar`: Wiedergabe, Warteschlange, Zufall,
  Wiederholen, Kapitel-Sprungliste
- `audiodesk/renamer.py`/`renamedialog.py` — Vorlagen-Umbenennung
- `audiodesk/mainwindow.py` — Hauptfenster, Musik-/Hörbuch-Tabs
- `audiodesk/config.py` — Einstellungen (QSettings + Schlüsselbund)
- `audiodesk/i18n.py` — Übersetzungstabelle

## Entwickeln

```bash
.venv/bin/pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen .venv/bin/pytest
```

Ein Teil der Tests erzeugt echte M4B-Testdateien mit eingebetteten
Kapitelmarken über `ffmpeg` (übersprungen, falls `ffmpeg` nicht
installiert ist) statt zu mocken.

Windows-Installer und macOS-Pakete entstehen per PyInstaller + Inno Setup
in CI, ausgelöst von einem Tag wie `v0.2.0` — siehe
[packaging/README.md](packaging/README.md). Anders als bei den
Geschwistern bleibt `PySide6.QtMultimedia` in der PyInstaller-Spec, das
macht die eigentliche Wiedergabe.

## Bekannte Grenzen

- Windows/macOS sind reines Qt/Python und sollten funktionieren, wurden
  aber nicht manuell auf diesen Plattformen getestet.
- Kapitelmarken werden nur aus dem Nero-Stil-Atom (`chpl`) gelesen, nicht
  aus dem selteneren QuickTime-Text-Track-Format.
- Discogs führt Interpret und Titel bei der Suche selbst noch in einem
  kombinierten Feld — sauber getrennt wird erst beim Übernehmen eines
  Treffers (Release-Detailaufruf).
- Kein Drag & Drop aus anderen Dateimanagern.

## Lizenz

[MIT](LICENSE). Verwendet [PySide6](https://doc.qt.io/qtforpython/)
inkl. QtMultimedia (LGPL), [mutagen](https://mutagen.readthedocs.io/)
(LGPL), [Send2Trash](https://github.com/arsenetar/send2trash) (BSD) und
[keyring](https://github.com/jaraco/keyring) (MIT). Metadaten stammen von
[MusicBrainz](https://musicbrainz.org) (Daten CC0), [Discogs](https://www.discogs.com/),
[Last.fm](https://www.last.fm/) und Apples iTunes Search API.
