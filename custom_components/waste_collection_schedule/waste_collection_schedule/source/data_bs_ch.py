from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Basel-Stadt"
DESCRIPTION = "Source for waste collection schedule of Basel-Stadt, Switzerland."
URL = "https://data.bs.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Zone A": {"zone": "A"},
    "Zone B": {"zone": "B"},
}

ICON_MAP = {
    "Kehrichtabfuhr": "mdi:trash-can",
    "Grünabfuhr": "mdi:leaf",
    "Papierabfuhr": "mdi:package-variant",
    "Grobsperrgut": "mdi:sofa",
    "Metallabfuhr": "mdi:iron-outline",
    "Häckseldienst": "mdi:tree",
    "Unbrennbares": "mdi:fire-off",
}

VALID_ZONES = ["A", "B", "C", "D", "E", "F", "G", "H", "GUF"]

API_URL = "https://data.bs.ch/api/records/1.0/search/"
DATASET = "100096"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your zone on the Basel-Stadt zone map at https://map.geo.bs.ch (search for 'Abfuhrzonen').",
    "de": "Finden Sie Ihre Zone auf der Basel-Stadt Zonenkarte unter https://map.geo.bs.ch (suchen Sie nach 'Abfuhrzonen').",
}

PARAM_DESCRIPTIONS = {
    "en": {"zone": "Your waste collection zone (A-H or GUF)."},
    "de": {"zone": "Ihre Abfuhrzone (A-H oder GUF)."},
}

PARAM_TRANSLATIONS = {
    "en": {"zone": "Zone"},
    "de": {"zone": "Zone"},
}


class Source:
    def __init__(self, zone: str):
        self._zone = zone.strip().upper()

        if self._zone not in VALID_ZONES:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", self._zone, suggestions=VALID_ZONES
            )

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        entries: list[Collection] = []

        for year in [now.year, now.year + 1] if now.month == 12 else [now.year]:
            params: dict[str, str | int] = {
                "dataset": DATASET,
                "rows": 500,
                "refine.zone": self._zone,
                "q": f"termin>={year}-01-01 AND termin<={year}-12-31",
                "sort": "termin",
            }
            r = requests.get(
                API_URL,
                params=params,
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()

            for rec in data.get("records", []):
                fields = rec.get("fields", {})
                date_str = fields.get("termin")
                waste_type = fields.get("art")

                if not date_str or not waste_type:
                    continue

                entries.append(
                    Collection(
                        date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
