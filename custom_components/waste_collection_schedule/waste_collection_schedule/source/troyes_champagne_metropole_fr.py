# coding: utf-8
"""
Waste Collection Schedule source for Troyes Champagne Métropole, France.

Currently supported calendar:
- Sainte-Savine Nord, 2026

Calendar: "Collecte de vos déchets 2026 - Sainte-Savine Nord"

Waste types:
- Ordures ménagères
- Tri
- Déchets verts
"""

from datetime import date

TITLE = "Troyes Champagne Métropole"
DESCRIPTION = "Collecte des déchets - Troyes Champagne Métropole"
URL = "https://troyes-champagne-metropole.fr"

TEST_CASES = {
    "Sainte-Savine Nord": {
        "commune": "Sainte-Savine",
        "secteur": "Nord",
    },
}

ICON_MAP = {
    "Ordures ménagères": "mdi:trash-can",
    "Tri": "mdi:recycle",
    "Déchets verts": "mdi:leaf",
}


SUPPORTED_CALENDARS = {
    ("sainte-savine", "nord"): {
        "Ordures ménagères": [
            "2026-01-07", "2026-01-14", "2026-01-21", "2026-01-28",
            "2026-02-04", "2026-02-11", "2026-02-18", "2026-02-25",
            "2026-03-04", "2026-03-11", "2026-03-18", "2026-03-25",
            "2026-04-01", "2026-04-08", "2026-04-15", "2026-04-22", "2026-04-29",
            "2026-05-06", "2026-05-13", "2026-05-20", "2026-05-27",
            "2026-06-03", "2026-06-10", "2026-06-17", "2026-06-24",
            "2026-07-01", "2026-07-08", "2026-07-15", "2026-07-22", "2026-07-29",
            "2026-08-05", "2026-08-12", "2026-08-19", "2026-08-26",
            "2026-09-02", "2026-09-09", "2026-09-16", "2026-09-23", "2026-09-30",
            "2026-10-07", "2026-10-14", "2026-10-21", "2026-10-28",
        ],
        "Tri": [
            "2026-01-02", "2026-01-08", "2026-01-15", "2026-01-22", "2026-01-29",
            "2026-02-05", "2026-02-12", "2026-02-19", "2026-02-26",
            "2026-03-05", "2026-03-12", "2026-03-19", "2026-03-26",
            "2026-04-02", "2026-04-09", "2026-04-16", "2026-04-23", "2026-04-30",
            "2026-05-07", "2026-05-14", "2026-05-21", "2026-05-28",
            "2026-06-04", "2026-06-11", "2026-06-18", "2026-06-25",
            "2026-07-02", "2026-07-09", "2026-07-16", "2026-07-23", "2026-07-30",
            "2026-08-06", "2026-08-13", "2026-08-20", "2026-08-27",
            "2026-09-03", "2026-09-10", "2026-09-17", "2026-09-24",
            "2026-10-01", "2026-10-08", "2026-10-15", "2026-10-22", "2026-10-29",
        ],
        "Déchets verts": [
            "2026-01-16",
            "2026-03-13",
            "2026-04-03", "2026-04-10", "2026-04-17", "2026-04-24",
            "2026-05-02", "2026-05-08", "2026-05-15", "2026-05-22", "2026-05-29",
            "2026-06-05", "2026-06-12", "2026-06-19", "2026-06-26",
            "2026-07-03", "2026-07-10", "2026-07-17", "2026-07-24", "2026-07-31",
            "2026-08-07", "2026-08-14", "2026-08-21", "2026-08-28",
            "2026-09-04", "2026-09-11", "2026-09-18", "2026-09-25",
            "2026-10-02", "2026-10-09", "2026-10-16", "2026-10-23", "2026-10-30",
        ],
    }
}


def _normalize(value):
    return value.strip().lower() if isinstance(value, str) else ""


class Source:
    def __init__(self, commune="Sainte-Savine", secteur="Nord"):
        self.commune = commune
        self.secteur = secteur

    def fetch(self):
        calendar_key = (_normalize(self.commune), _normalize(self.secteur))

        if calendar_key not in SUPPORTED_CALENDARS:
            raise ValueError(
                "Only Sainte-Savine / Nord is currently supported by this source."
            )

        entries = []
        for waste_type, dates in SUPPORTED_CALENDARS[calendar_key].items():
            for collection_date in dates:
                entries.append((date.fromisoformat(collection_date), waste_type))

        return sorted(entries, key=lambda item: item[0])
