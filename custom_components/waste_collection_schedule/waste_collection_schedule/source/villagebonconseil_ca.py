import datetime
import html
import re

import requests
from waste_collection_schedule import Collection

TITLE = "Notre-Dame-du-Bon-Conseil (Village)"
DESCRIPTION = "Source for villagebonconseil.ca waste collection calendar"
URL = "https://villagebonconseil.ca"
COUNTRY = "ca"
TEST_CASES = {"Village": {}}

ICON_MAP = {
    "Ordures ménagères": "mdi:trash-can",
    "Matières organiques": "mdi:leaf",
    "Matières recyclables": "mdi:recycle",
    "Conteneur en métal – Déchets": "mdi:dumpster",
    "Conteneur en métal – Recyclage": "mdi:recycle",
    "Encombrants": "mdi:sofa",
}

WASTE_TYPE_MAP = {
    "Collecte des ordures ménagères (bac noir)": "Ordures ménagères",
    "Collecte des matières organiques (bac brun)": "Matières organiques",
    "Collecte des matières recyclables (bac vert)": "Matières recyclables",
    "Collecte des matières recyclables (bac vert et bleu)": "Matières recyclables",
    "Collecte conteneur en métal – Déchets": "Conteneur en métal – Déchets",
    "Collecte conteneur en métal / Déchets": "Conteneur en métal – Déchets",
    "Collecte conteneur en métal – Recyclage": "Conteneur en métal – Recyclage",
    "Collecte conteneur en métal / Recyclage": "Conteneur en métal – Recyclage",
    "Collecte des encombrants": "Encombrants",
}

PAGE_URL = (
    "https://villagebonconseil.ca/services-aux-citoyens/environnement/"
    "collecte-des-matieres-residuelles/"
)


class Source:
    def __init__(self):
        pass

    def fetch(self) -> list[Collection]:
        r = requests.get(PAGE_URL, timeout=30)
        r.raise_for_status()

        match = re.search(r"var eventscalendar\s*=\s*(\[[\s\S]*?\]);", r.text)
        if not match:
            raise ValueError("Could not find calendar data on the page")

        raw_data = match.group(1)

        entries = []
        pattern = r"\{[^{}]*'Date':\s*new\s*Date\((\d+),\s*(\d+),\s*(\d+)\)[^{}]*'Title':\s*'([^']*)'[^{}]*\}"

        for m in re.finditer(pattern, raw_data):
            year = int(m.group(1))
            month = int(m.group(2)) + 1
            day = int(m.group(3))
            title_html = m.group(4)

            collection_date = datetime.date(year, month, day)

            title_match = re.search(r'title="([^"]*)"', title_html)
            if not title_match:
                continue
            raw_type = title_match.group(1)
            raw_type = html.unescape(raw_type)
            raw_type = raw_type.strip()

            waste_type = None
            for key, value in WASTE_TYPE_MAP.items():
                if raw_type == key:
                    waste_type = value
                    break
            if waste_type is None:
                waste_type = raw_type

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        if not entries:
            raise ValueError("No collection entries found")

        return entries
