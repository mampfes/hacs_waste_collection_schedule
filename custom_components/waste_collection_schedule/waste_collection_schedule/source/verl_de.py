import re

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadt Verl"
DESCRIPTION = "Source for Stadt Verl waste collection."
URL = "https://www.verl.de"
COUNTRY = "de"

TEST_CASES = {
    "Abfuhrbezirk 1": {"bezirk": 1},
    "Abfuhrbezirk 3": {"bezirk": 3},
    "Abfuhrbezirk 5": {"bezirk": 5},
}

PARAM_TRANSLATIONS = {
    "en": {"bezirk": "Collection district"},
    "de": {"bezirk": "Abfuhrbezirk"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "bezirk": "Your collection district number (1-5). Find yours at https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke"
    },
    "de": {
        "bezirk": "Ihre Abfuhrbezirksnummer (1-5). Ermitteln Sie Ihren Bezirk unter https://www.verl.de/rathaus/aktuelles/digitaler-umweltkalender/abfallbezirke"
    },
}

ICON_MAP = {
    "Restmülltonne": Icons.GENERAL_WASTE,
    "Komposttonne": Icons.ORGANIC,
    "Papiertonne": Icons.PAPER,
    "Gelbe Tonne": Icons.RECYCLING,
    "Gartenabfallannahme": Icons.ORGANIC,
    "Wertstoffhof": Icons.RECYCLING,
    "Giftmobil": Icons.GENERAL_WASTE,
}

CALENDAR_URL = (
    "https://www.verl.de/service/abfallentsorgung/umwelt-und-abfallkalender.html"
)
ENDPOINT_PATH = "/?middlewareAction=createWastecalendarIcs"


class Source:
    def __init__(self, bezirk: int):
        self._bezirk = int(bezirk)
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )

        resp = session.get(CALENDAR_URL)
        resp.raise_for_status()

        key_match = re.search(r"middlewareKey=([A-Za-z0-9]+)", resp.text)
        if not key_match:
            raise ValueError("Could not find middleware key on Verl calendar page")
        middleware_key = key_match.group(1)

        page_id_match = re.search(r'name="id"\s+value="(\d+)"', resp.text)
        page_id = page_id_match.group(1) if page_id_match else "50"

        endpoint = f"https://www.verl.de{ENDPOINT_PATH}&middlewareKey={middleware_key}"

        data = {
            "id": page_id,
            f"bezirk{self._bezirk}": "on",
            "abfall1": "on",
            "abfall2": "on",
            "abfall3": "on",
            "abfall4": "on",
            "abfuhr_tag": "0",
            "individuell": "Auswahl laden",
        }

        ics_resp = session.post(endpoint, data=data, headers={"Referer": CALENDAR_URL})
        ics_resp.raise_for_status()

        dates = self._ics.convert(ics_resp.text)

        entries = []
        for d in dates:
            icon = None
            for key, val in ICON_MAP.items():
                if key in d[1]:
                    icon = val
                    break
            entries.append(Collection(d[0], d[1], icon))
        return entries
