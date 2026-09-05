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

<h2>Welche Quelle wofuer?</h2>
<p>Alle vier Quellen sind optional und lassen sich einzeln unter
<b>Einstellungen &rarr; Quellen</b> ein- und ausschalten. MusicBrainz,
Discogs und Last.fm sind reine <b>Musik</b>datenbanken und werden fuer
Hoerbuch-Kapitel gar nicht erst befragt (siehe naechster Abschnitt) - dafuer
gibt es die eigene iTunes-Hoerbuch-Quelle.</p>

<h3>MusicBrainz (Musik) - empfohlen, kein Key noetig</h3>
<p>Titel, Interpret, Album und ein Cover (ueber das Cover Art Archive),
gesucht ueber Titel und Interpret.</p>

<h3>Discogs (Musik) - Zweitquelle, braucht einen kostenlosen Zugriffs-Token</h3>
<ol>
<li>Konto auf <a href="https://www.discogs.com">discogs.com</a> anlegen.</li>
<li>Unter <a href="https://www.discogs.com/settings/developers">discogs.com/settings/developers</a>
    einen <b>persoenlichen Zugriffs-Token</b> erzeugen (kein OAuth noetig).</li>
<li>Den Token in <b>Einstellungen &rarr; Discogs</b> eintragen.</li>
</ol>
<p>Discogs fuehrt Interpret und Titel in einem einzigen Feld
("Interpret - Titel") - die Trennung ist deshalb ein Ratewert und nicht
immer exakt.</p>

<h3>Last.fm (Musik) - Zweitquelle, braucht einen kostenlosen API-Key</h3>
<ol>
<li>API-Key anfordern unter <a href="https://www.last.fm/api/account/create">last.fm/api/account/create</a>.</li>
<li>Den Key in <b>Einstellungen &rarr; Last.fm</b> eintragen.</li>
</ol>

<h3>iTunes (Hoerbuecher) - einzige Hoerbuch-Quelle, kein Key noetig</h3>
<p>Apples oeffentliche iTunes-Suche kennt eine eigene Hoerbuch-Kategorie und
liefert Titel, Autor (als "Interpret" gefuehrt) und Cover. Per Vorgabe
aktiv. Die Abdeckung ist trotzdem nicht vollstaendig - nicht jedes Hoerbuch
steht im iTunes Store, unsichere oder fehlende Treffer bleiben markiert und
lassen sich per <i>Manuell zuordnen</i> nachtragen.</p>
<p><b>Nicht eingebaut ist Audible</b>: Audible bietet keine oeffentliche API
an, ein Zugriff liefe nur ueber Scraping der Webseite gegen deren
Nutzungsbedingungen - das macht audiodesk bewusst nicht, auch nicht ueber
importierte Skripte anderer Tools.</p>

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
