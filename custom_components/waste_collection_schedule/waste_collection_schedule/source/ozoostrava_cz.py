from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "OZO Ostrava"
DESCRIPTION = "Waste collection schedules for Ostrava and nearby municipalities"
URL = "https://ozoostrava.cz"

TEST_CASES = {
    "Ostrava Poruba": {
        "municipality": "Ostrava",
        "district": "Poruba",
        "street": "Hlavní třída",
        "house_number": "583",
    },
    "Hladké Životice": {
        "municipality": "Hladké Životice",
        "district": "Hladké Životice",
        "street": "Hlavní",
        "house_number": "12",
    },
}

ICON_MAP = {
    "bio": "mdi:leaf",
    "papír": "mdi:package-variant",
    "plasty": "mdi:recycle",
    "směsný odpad": "mdi:trash-can",
    "sklo": "mdi:bottle-soda",
    "singlestream": "mdi:recycle-variant",
}


class Source:
    def __init__(
        self, municipality: str, district: str, street: str, house_number: str
    ):
        self._obec = municipality
        self._obvod = district
        self._ulice = street
        self._cislo = house_number

    def fetch(self):
        params = {
            "obec": self._obec,
            "obvod": self._obvod,
            "ulice": self._ulice,
            "cisp": self._cislo,
            "druh": -1,
        }

        r = requests.get(f"{URL}/svoz2.php", params=params, timeout=30)
        r.raise_for_status()

        data = r.json()
        entries = []

        for date_str, waste in data.items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                waste_types = (
                    list(waste.keys())
                    if isinstance(waste, dict)
                    else (waste if isinstance(waste, list) else [])
                )

                for type_name in waste_types:
                    if type_name.lower() in ["velikonoce", "vánoce"]:
                        continue

                    entries.append(
                        Collection(
                            date=date_obj,
                            t=type_name,
                            icon=ICON_MAP.get(type_name.lower(), "mdi:trash-can"),
                        )
                    )
            except (ValueError, TypeError):
                continue

        return entries
