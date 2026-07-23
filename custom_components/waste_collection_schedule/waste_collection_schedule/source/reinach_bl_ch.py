"""Source for Reinach BL, Switzerland."""

import re
from datetime import datetime
from xml.etree import ElementTree

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Reinach BL"
DESCRIPTION = (
    "Source for waste collection schedule of Gemeinde Reinach BL, Switzerland."
)
URL = "https://www.reinach-bl.ch"
COUNTRY = "ch"

RSS_URL = "https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender/rss.php"

VALID_ZONES = ["Kreis Ost", "Kreis West"]

TEST_CASES = {
    "Kreis Ost": {"zone": "Kreis Ost"},
    "Kreis West": {"zone": "Kreis West"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Select your collection zone (Kreis Ost or Kreis West). "
        "You can find your zone on the official Reinach BL waste calendar "
        "page at https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender."
    ),
    "de": (
        "Wählen Sie Ihren Abfuhrkreis (Kreis Ost oder Kreis West). "
        "Den Kreis finden Sie auf dem Abfallkalender der Gemeinde Reinach BL "
        "unter https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"zone": "Collection zone"},
    "de": {"zone": "Abfuhrkreis"},
}

PARAM_DESCRIPTIONS = {
    "en": {"zone": "Collection zone: 'Kreis Ost' or 'Kreis West'."},
    "de": {"zone": "Abfuhrkreis: 'Kreis Ost' oder 'Kreis West'."},
}

ICON_MAP = {
    "Hauskehricht": Icons.GENERAL_WASTE,
    "Grünabfuhr/Bioabfall": Icons.BIO_KITCHEN,
    "Häckseldienst": Icons.GARDEN,
    "Papier": Icons.PAPER,
    "Karton": Icons.PAPER,
    "Metalle": Icons.METAL,
}


class Source:
    def __init__(self, zone: str):
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone",
                zone,
                suggestions=VALID_ZONES,
            )
        self._zone = zone

    def fetch(self) -> list[Collection]:
        response = requests.get(RSS_URL, timeout=30)
        response.raise_for_status()

        root = ElementTree.fromstring(response.content)

        entries: list[Collection] = []
        for item in root.iter("item"):
            title_el = item.find("title")
            description_el = item.find("description")
            if title_el is None or description_el is None:
                continue

            waste_type = (title_el.text or "").strip()
            description = (description_el.text or "").strip()

            # Description format: "DD.MM.YYYY<br/>Zone: Kreis Ost"
            date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", description)
            zone_match = re.search(r"Zone:\s*(.+?)\s*$", description)

            if not date_match or not zone_match:
                continue

            zone = zone_match.group(1).strip()
            if zone != self._zone:
                continue

            try:
                collection_date = datetime.strptime(
                    date_match.group(0), "%d.%m.%Y"
                ).date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
