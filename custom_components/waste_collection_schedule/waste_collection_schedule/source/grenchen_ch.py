import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Grenchen (CH)"
DESCRIPTION = "Source for waste collection in Grenchen, Switzerland."
URL = "https://www.grenchen.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Zone Ost": {"zone": "Zone Ost"},
    "Zone West": {"zone": "Zone West"},
}

ICON_MAP = {
    "Grünabfälle": "mdi:leaf",
    "Karton": "mdi:package-variant",
    "Altpapier": "mdi:newspaper",
    "Altglas": "mdi:glass-fragile",
    "Altmetall": "mdi:nail",
}

LOCALCITIES_URL = "https://www.localcities.ch/de/entsorgung/grenchen/3533"

VALID_ZONES = ["Zone Ost", "Zone West"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your zone (Zone Ost or Zone West). Check <a href='https://www.localcities.ch/de/entsorgung/grenchen/3533'>localcities.ch</a> to find your zone.",
    "de": "Wählen Sie Ihre Zone (Zone Ost oder Zone West). Auf <a href='https://www.localcities.ch/de/entsorgung/grenchen/3533'>localcities.ch</a> finden Sie Ihre Zone.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone (Zone Ost or Zone West)",
    },
    "de": {
        "zone": "Abfuhrzone (Zone Ost oder Zone West)",
    },
}


class Source:
    def __init__(self, zone: str):
        zone = zone.strip()
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions("zone", zone, VALID_ZONES)
        self._zone = zone

    def fetch(self) -> list[Collection]:
        r = requests.get(LOCALCITIES_URL)
        r.raise_for_status()
        r.encoding = "utf-8"

        soup = BeautifulSoup(r.text, "html.parser")
        today = date.today()
        entries = []

        date_divs = soup.find_all("div", class_="waste-calender-list__date")

        for date_div in date_divs:
            h2 = date_div.find("h2")
            if not h2:
                continue
            date_text = h2.get_text(strip=True)

            if date_text == "Heute":
                collection_date = today
            elif date_text == "Morgen":
                collection_date = today + timedelta(days=1)
            else:
                try:
                    day, month = date_text.split(".")
                    collection_date = date(today.year, int(month), int(day))
                    if collection_date < today - timedelta(days=30):
                        collection_date = collection_date.replace(year=today.year + 1)
                except (ValueError, IndexError):
                    continue

            parent_row = date_div.parent
            items = parent_row.find_all(
                "div", class_=re.compile(r"list-calendar-item--")
            )

            for item in items:
                zone_text = item.get_text(strip=True)
                if zone_text != self._zone:
                    continue

                img = item.find("img", alt=True)
                if not img:
                    continue

                waste_type = img["alt"]
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
