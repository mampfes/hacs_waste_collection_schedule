from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Marktgemeinde Eggelsberg"
DESCRIPTION = "Source for Marktgemeinde Eggelsberg waste collection."
URL = "https://www.eggelsberg.at"
COUNTRY = "at"

TEST_CASES = {
    "Zone A": {"zone": "A"},
    "Zone B": {"zone": "B"},
}

ICON_MAP = {
    "Bioabfall": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
    "Restabfall 2-wöchentlich": "mdi:trash-can",
    "Restabfall 4-wöchentlich": "mdi:trash-can",
    "Restabfall 6-wöchentlich": "mdi:trash-can",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select your zone (A or B). This determines your Bioabfall (organic waste) "
    "collection schedule. All other waste types apply to all zones.",
    "de": "Wählen Sie Ihre Zone (A oder B). Dies bestimmt Ihren Bioabfall-"
    "Abholplan. Alle anderen Abfallarten gelten für alle Zonen.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone (A or B)",
    },
    "de": {
        "zone": "Abholzone (A oder B)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "zone": "Zone",
    },
    "de": {
        "zone": "Zone",
    },
}

VALID_ZONES = ["A", "B"]
CALENDAR_URL = "https://www.eggelsberg.at/system/web/kalender.aspx"
MENU_ONR = "224085238"
MAX_PAGES = 10


class Source:
    def __init__(self, zone: str):
        zone = zone.strip().upper()
        if zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", zone, suggestions=VALID_ZONES
            )
        self._zone = zone

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []
        seen: set[tuple[str, str, str]] = set()
        today = datetime.now().strftime("%d.%m.%Y")

        for page in range(MAX_PAGES):
            params = {
                "bdatum": "31.12.9999",
                "blnr": "",
                "gnr_search": "0",
                "menuonr": MENU_ONR,
                "page": str(page),
                "umkreis": "",
                "useronr": "0",
                "vdatum": today,
            }
            r = requests.get(CALENDAR_URL, params=params, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            rows = [
                tr
                for tr in soup.find_all("tr")
                if tr.find_all("td") and len(tr.find_all("td")) >= 3
            ]

            if not rows:
                break

            # Detect pagination loop (server repeats page 0 after last page)
            first_row_key = tuple(
                td.get_text(strip=True) for td in rows[0].find_all("td")[:3]
            )
            if first_row_key in seen:
                break
            seen.add(first_row_key)

            for row in rows:
                tds = row.find_all("td")
                date_text = tds[0].get_text(strip=True)
                waste_type = tds[1].get_text(strip=True)
                zone = tds[2].get_text(strip=True)

                if zone not in ("Gemeinde Alle", self._zone):
                    continue

                date_part = date_text.split("(")[0].strip()
                try:
                    date = datetime.strptime(date_part, "%d.%m.%Y").date()
                except ValueError:
                    continue

                icon = ICON_MAP.get(waste_type)
                entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
