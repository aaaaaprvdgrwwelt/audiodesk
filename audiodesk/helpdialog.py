"""Hilfe: was audiodesk kann und wie der Online-Abgleich funktioniert."""
from __future__ import annotations

from deskkit.helpdialog import HelpDialog as _HelpDialog

from .i18n import _

HELP_HTML = """
<h2>Erste Schritte</h2>
<ol>
<li>Ueber <b>Ordner hinzufuegen</b> einen Musik- und/oder Hoerbuch-Ordner
    angeben - beide werden getrennt gefuehrt, damit Musik nicht versehentlich
    als Hoerbuch-Kapitel landet und umgekehrt.</li>
<li><b>Scannen</b> liest die Ordner ein - Titel/Interpret/Album/Cover kommen
    dabei aus den eingebetteten Tags (ID3, MP4, FLAC, Vorbis).</li>
<li><b>Automatisch zuordnen</b> ergaenzt fehlende Angaben und ein Cover
    ueber <a href="https://musicbrainz.org">MusicBrainz</a> - kostenlos,
    kein API-Key noetig. Unsichere oder fehlgeschlagene Treffer bleiben
    markiert und lassen sich per Rechtsklick &rarr; <i>Manuell zuordnen</i>
    von Hand nachtragen.</li>
<li>Doppelklick oder <b>Abspielen</b> startet die Wiedergabeleiste am
    unteren Fensterrand. Bei Hoerbuechern wird die Position gemerkt.</li>
</ol>

<h2>Was MusicBrainz liefert - und wo es an Grenzen stoesst</h2>
<p>Fuer Musik: Titel, Interpret, Album und ein Cover (ueber das Cover Art
Archive), gesucht ueber Titel und Interpret. Fuer Hoerbuecher ist die
Abdeckung bei MusicBrainz deutlich luecklicher, da es in erster Linie eine
Musikdatenbank ist - ein Treffer ist dort keine Garantie.</p>

<h2>Musik-Ordner vs. Hoerbuch-Ordner</h2>
<p>Beide Ordnerarten werden getrennt in den Einstellungen gepflegt. Eine
automatische Erkennung anhand der Datei allein waere unzuverlaessig -
deshalb legt der Ordner fest, ob eine Datei als Musikstueck (zu einem Album
gruppiert) oder als Hoerbuch-Kapitel (zu einem Hoerbuch gruppiert, meist
ueber den Album-Tag oder sonst den Ordnernamen) gefuehrt wird.</p>

<h2>Kapitelmarken bei M4B</h2>
<p>Liegt ein Hoerbuch als eine einzelne M4B-Datei mit eingebetteten
Kapitelmarken vor, werden diese (falls auslesbar) nicht einzeln als
Bibliothekseintraege gefuehrt - die Datei wird als ein durchgehendes Stueck
abgespielt.</p>

<h2>Umbenennen-Vorlagen</h2>
<p>Unter <b>Einstellungen &rarr; Umbenennen</b> frei einstellbar, getrennt fuer
Musik (<code>{artist} {album} {track_number} {title} {year} {ext}</code>)
und Hoerbuecher (<code>{book_title} {chapter} {title} {ext}</code>). Ein
<code>/</code> in der Vorlage legt eine neue Ordnerebene an.</p>

<h2>Loeschen</h2>
<p>Verschiebt Dateien in den Papierkorb, nichts wird endgueltig geloescht.</p>

<h2>Wo Daten liegen</h2>
<table cellpadding="4">
<tr><td>Einstellungen</td><td><code>~/.config/audiodesk/audiodesk.conf</code></td></tr>
<tr><td>Bibliotheksindex (Zuordnungen, Wiedergabefortschritt)</td>
    <td><code>~/.local/share/audiodesk/library.sqlite</code></td></tr>
<tr><td>Antwort-Cache, Cover</td><td><code>~/.cache/audiodesk/</code></td></tr>
</table>
"""


class HelpDialog(_HelpDialog):
    def __init__(self, parent=None):
        super().__init__(HELP_HTML, _("Hilfe"), parent)
