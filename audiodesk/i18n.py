"""Sprachumschaltung.

Der Mechanismus (aktive Sprache verfolgen, Systemsprache erkennen, in der
Tabelle nachschlagen) steckt in `deskkit.i18n.Translator` - geteilt mit den
anderen *desk-Apps. Hier liegt nur die App-eigene Uebersetzungstabelle.
"""
from __future__ import annotations

from deskkit.i18n import LANGUAGES, Translator, system_language

__all__ = ["LANGUAGES", "system_language", "set_language", "language", "_"]

# ---------------------------------------------------------------------------
DE = {
    # Nur Eintraege, bei denen der ASCII-Schluessel Umlaute braucht.
    "Loeschen": "Löschen",
    "Loeschen …": "Löschen …",
    "Ordner hinzufuegen …": "Ordner hinzufügen …",
    "Ordner waehlen": "Ordner wählen",
    "Bitte mindestens einen Ordner hinzufuegen.":
        "Bitte mindestens einen Ordner hinzufügen.",
    "Bitte mindestens eine Datei waehlen.": "Bitte mindestens eine Datei wählen.",
    "Bitte genau einen Eintrag waehlen.": "Bitte genau einen Eintrag wählen.",
    "Waehlen …": "Wählen …",
    "Einstellungen …": "Einstellungen …",
    "Automatisch zuordnen": "Automatisch zuordnen",
    "Umbenennen …": "Umbenennen …",
    "Kein API-Key hinterlegt.": "Kein API-Key hinterlegt.",
    "Nicht konfiguriert": "Nicht konfiguriert",
    "ueberspringen": "überspringen",
    "Uebernehmen": "Übernehmen",
    "Schliessen": "Schließen",
    "Zurueck": "Zurück",
    "Weiter": "Weiter",
    "Kein Eintrag ausgewaehlt": "Kein Eintrag ausgewählt",
    "Scan abgeschlossen.": "Scan abgeschlossen.",
    "Datei nicht gefunden - eventuell verschoben oder geloescht.":
        "Datei nicht gefunden - eventuell verschoben oder gelöscht.",
    "Nicht alles konnte geloescht werden:": "Nicht alles konnte gelöscht werden:",
    "Alle Alben": "Alle Alben",
    "Treffer waehlen": "Treffer wählen",
    "von Hand gewaehlt": "von Hand gewählt",
    "Schwellwert fuer automatische Zuordnung":
        "Schwellwert für automatische Zuordnung",
    "Aktiv (kein API-Key noetig)": "Aktiv (kein API-Key nötig)",
}
EN: dict[str, str] = {}

TABLE = {"de": DE, "en": EN}

_translator = Translator(TABLE)
_ = _translator
set_language = _translator.set_language
language = _translator.language
