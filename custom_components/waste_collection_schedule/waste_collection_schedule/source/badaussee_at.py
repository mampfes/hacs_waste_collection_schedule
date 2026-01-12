import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Bad Aussee"
DESCRIPTION = "Source for Bad Aussee, Austria"
URL = "https://www.badaussee.at"
TEST_CASES = {
    "Zone 4": {
        "restmuell_zone": "4",
        "biomuell_zone": "4",
        "altpapier_zone": "1",
    },
}

API_URL = "https://www.badaussee.at/system/web/kalender.aspx"

# Mapping of type IDs to their waste types
TYPE_IDS = {
    "gelber_sack": "225238770",
    "restmuell": "225262538",
    "biomuell": "225262564",
    "altpapier": "225262565",
}

ICON_MAP = {
    "Gelber Sack": "mdi:sack",
    "Restmüllzone": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "restmuell_zone": "Zone number for residual waste (Restmüll)",
        "biomuell_zone": "Zone number for organic waste (Biomüll)",
        "altpapier_zone": "Zone number for paper waste (Altpapier)",
    },
    "de": {
        "restmuell_zone": "Zonennummer für Restmüll",
        "biomuell_zone": "Zonennummer für Biomüll",
        "altpapier_zone": "Zonennummer für Altpapier",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "restmuell_zone": "Residual Waste Zone",
        "biomuell_zone": "Organic Waste Zone",
        "altpapier_zone": "Paper Waste Zone",
    },
    "de": {
        "restmuell_zone": "Restmüll Zone",
        "biomuell_zone": "Biomüll Zone",
        "altpapier_zone": "Altpapier Zone",
    },
}


class Source:
    def __init__(
        self,
        restmuell_zone: str | int = "",
        biomuell_zone: str | int = "",
        altpapier_zone: str | int = "",
    ):
        self._restmuell_zone = str(restmuell_zone) if restmuell_zone else ""
        self._biomuell_zone = str(biomuell_zone) if biomuell_zone else ""
        self._altpapier_zone = str(altpapier_zone) if altpapier_zone else ""

    def fetch(self) -> list[Collection]:
        # Build the type IDs parameter based on provided zones
        type_ids = [TYPE_IDS["gelber_sack"]]  # Always include Gelber Sack

        if self._restmuell_zone:
            type_ids.append(TYPE_IDS["restmuell"])
        if self._biomuell_zone:
            type_ids.append(TYPE_IDS["biomuell"])
        if self._altpapier_zone:
            type_ids.append(TYPE_IDS["altpapier"])

        params = {
            "sprache": "1",
            "menuonr": "225254344",
            "typids": ",".join(type_ids),
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find the table with collection schedule
        table = soup.find("table", {"class": "ris_table"})
        if not table:
            raise Exception("Could not find collection schedule table")

        entries = []

        # Process table rows (skip header)
        rows = table.find_all("tr")
        if not rows:
            raise Exception("No data rows found in collection schedule")

        # Extract data from rows
        for row in rows[1:]:  # Skip header row
            cols = row.find_all(["td", "th"])
            if len(cols) < 2:
                continue

            date_text = cols[0].get_text(strip=True)
            waste_type_text = cols[1].get_text(strip=True)

            # Parse date (format: "DD.MM.YYYY (Weekday)")
            date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_text)
            if not date_match:
                continue

            date_str = date_match.group(1)
            date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

            # Filter based on zones
            if not self._should_include_entry(waste_type_text):
                continue

            # Determine icon
            icon = None
            for key, value in ICON_MAP.items():
                if key in waste_type_text:
                    icon = value
                    break

            entries.append(
                Collection(
                    date=date,
                    t=waste_type_text,
                    icon=icon,
                )
            )

        return entries

    def _should_include_entry(self, waste_type: str) -> bool:
        """Check if entry should be included based on configured zones."""
        # Always include Gelber Sack
        if "Gelber Sack" in waste_type:
            return True

        # Check Restmüll zone
        if "Restmüll" in waste_type and self._restmuell_zone:
            if f"Zone {self._restmuell_zone}" in waste_type or f"zone {self._restmuell_zone}" in waste_type.lower():
                return True
            return False

        # Check Biomüll zone
        if "Biomüll" in waste_type and self._biomuell_zone:
            if f"Zone {self._biomuell_zone}" in waste_type or f"zone {self._biomuell_zone}" in waste_type.lower():
                return True
            return False

        # Check Altpapier zone
        if "Altpapier" in waste_type and self._altpapier_zone:
            if f"Zone {self._altpapier_zone}" in waste_type or f"zone {self._altpapier_zone}" in waste_type.lower():
                return True
            return False

        return False
