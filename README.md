# AudioDesk

Ein Dateimanager, der nur Audio kennt: Musik und Hörbücher sichten, hören,
Metadaten holen, umbenennen, löschen. Python + Qt (PySide6), auf demselben
[deskkit](https://github.com/aaaaaprvdgrwwelt/deskkit)-Fundament wie
[MovieDesk](https://github.com/aaaaaprvdgrwwelt/moviedesk),
[ComicDesk](https://github.com/aaaaaprvdgrwwelt/comicdesk) und
[BookDesk](https://github.com/aaaaaprvdgrwwelt/bookdesk).

Musik (Album/Track) und Hörbücher (Buch/Kapitel) leben in einer
gemeinsamen Bibliothek, mit einer dauerhaften Wiedergabeleiste statt einem
Reader-Fenster. Metadaten kommen zuerst aus den eingebetteten Tags
(MP3/ID3, MP4/M4B, FLAC, OGG - über [mutagen](https://mutagen.readthedocs.io/)),
ergänzt durch einen optionalen Abgleich gegen
[MusicBrainz](https://musicbrainz.org) (kostenlos, kein API-Key nötig).

> Status: in aktiver Entwicklung, jung.

## Aus dem Quelltext starten

```bash
git clone https://github.com/aaaaaprvdgrwwelt/audiodesk.git
git clone https://github.com/aaaaaprvdgrwwelt/deskkit.git
cd audiodesk
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./audiodesk.sh
```

`deskkit` muss dafür als Geschwister-Ordner neben `audiodesk/` liegen
(siehe `requirements.txt`, `-e ../deskkit`).

## Bedienung

Siehe den Hilfe-Dialog in der App (`F1`) für Ersteinrichtung und
Tastenkürzel.
