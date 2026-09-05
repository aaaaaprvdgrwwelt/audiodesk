"""Eigene Icons als SVG.

Der Render-Mechanismus steckt in `deskkit.icons.IconSet` - geteilt mit den
anderen *desk-Apps. Hier liegt nur die App-eigene Icon-Tabelle.
"""
from __future__ import annotations

from deskkit.icons import IconSet

#: Strichzeichnungen auf einem 24x24-Raster.
PATHS = {
    "refresh": '<path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4h-4"/>',
    "help": '<circle cx="12" cy="12" r="9"/>'
            '<path d="M9.3 9.3a2.7 2.7 0 1 1 3.8 2.5c-.8.4-1.1 1-1.1 1.9"/>'
            '<circle cx="12" cy="17" r="0.1" stroke-width="2.4"/>',
    "match": '<path d="M11 3H4a1 1 0 0 0-1 1v7l9.5 9.5a1.5 1.5 0 0 0 2.1 0l6-6a1.5 1.5 0 0 0 0-2.1z"/>'
             '<circle cx="7.5" cy="7.5" r="1.4"/>',
    "rename": '<path d="M4 20h5l9.5-9.5a2.1 2.1 0 0 0-3-3L6 17z"/><path d="M14.5 6.5l3 3"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>',
    "folder_new": '<path d="M3 7a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>'
                  '<path d="M12 11v5M9.5 13.5h5"/>',
    "folder": '<path d="M3 7a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>',
    "delete": '<path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
              '<path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/>'
              '<path d="M10 11v6M14 11v6"/>',
    "settings": '<circle cx="12" cy="12" r="3"/>'
                '<path d="M12 2.5v3M12 18.5v3M21.5 12h-3M5.5 12h-3'
                'M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1M18.7 18.7l-2.1-2.1M7.4 7.4L5.3 5.3"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
    "check": '<path d="M4 12.5l5 5L20 6"/>',
    "warn": '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.2v.1"/>',
    "left": '<path d="M19 12H6M12 6l-6 6 6 6"/>',
    "right": '<path d="M5 12h13M12 6l6 6-6 6"/>',
    "music": '<circle cx="7" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'
             '<path d="M10 18V5l11-2v13"/>',
    "book": '<path d="M4 5.5A2 2 0 0 1 6 4h4.5a2 2 0 0 1 2 2v13a1.5 1.5 0 0 0-1.5-1.5H6a2 2 0 0 1-2-2z"/>'
            '<path d="M20 5.5A2 2 0 0 0 18 4h-4.5a2 2 0 0 0-2 2v13a1.5 1.5 0 0 1 1.5-1.5H18a2 2 0 0 0 2-2z"/>',
    "play": '<circle cx="12" cy="12" r="9"/><path d="M10 8.5l6 3.5-6 3.5z"/>',
    "pause": '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7M14 8.5v7"/>',
    "prev": '<path d="M18 6v12L8 12z"/><path d="M6 6v12"/>',
    "next": '<path d="M6 6v12l10-6z"/><path d="M18 6v12"/>',
    "volume": '<path d="M4 10v4h4l5 4V6l-5 4z"/><path d="M16.5 9.5a4 4 0 0 1 0 5"/>',
    "shuffle": '<path d="M4 6h3.5l9 12H20"/><path d="M4 18h3.5l2.3-3.1"/>'
               '<path d="M13.2 8.5L15.5 6H20"/>'
               '<path d="M17.5 3.5L20.5 6l-3 2.5"/><path d="M17.5 20.5l3-2.5-3-2.5"/>',
    "repeat": '<path d="M6 8h11a2 2 0 0 1 2 2v2"/><path d="M17.5 5.5L20 8l-2.5 2.5"/>'
              '<path d="M18 16H7a2 2 0 0 1-2-2v-2"/><path d="M6.5 18.5L4 16l2.5-2.5"/>',
    "queue": '<path d="M4 6h16M4 12h10M4 18h10"/><path d="M17 15v6M14 18h6"/>',
}

icon = IconSet(PATHS).icon
