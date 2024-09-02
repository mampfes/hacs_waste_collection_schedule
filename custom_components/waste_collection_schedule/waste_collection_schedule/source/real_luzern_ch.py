import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Real Luzern"
DESCRIPTION = "Source script for Real Luzern, Switzerland"
URL = "https://www.real-luzern.ch"

TEST_CASES = {
    "Luzern - Heimatweg": {"municipality_id": 13, "street_id": 766},
    "Luzern - Pliatusblick": {"municipality_id": 13, "street_id": 936},
    "Emmen": {"municipality_id": 6},
}

ICON_MAP = {
    "Kehricht": "mdi:trash-can",
    "Grüngut": "mdi:leaf",
    "Papier": "mdi:newspaper-variant-multiple",
    "Karton": "mdi:package-variant",
    "Altmetall": "mdi:clippy",
    # "Altmetall": "mdi:engine",
}

OLD_WASTE_NAME = (
    {  # New fetcher uses different names this should prevent breaking changes
        "Kehrichtsammlung": "Kehricht",
        "Grüngutsammlung": "Grüngut",
        "Papiersammlung": "Papier",
        "Kartonsammlung": "Karton",
        "Alteisen/Metallsammlung": "Altmetall",
    }
)

API_URL = "https://www.real-luzern.ch/abfall/sammeldienst/abfallkalender/"


class Source:
    def __init__(self, municipality_id: str | int, street_id: str | int | None = None):
        self._municipality_id = municipality_id
        self._street_id = street_id
        self._ics = ICS()
        self._ics_params: dict[str, str] | None = None

    def fetch_ics_params(self) -> None:
        uri = f"{API_URL}?gemid={self._municipality_id}&strid={self._street_id}"
        r = requests.get(uri)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        data_div = soup.select_one("div.abfk-calendar.abfk-colors")
        if not data_div:
            raise ValueError("No data found")

        tour_id = data_div.get("data-tourid", None)
        if not tour_id:
            raise ValueError("No tour id found")
        categories = data_div.get("data-categories", None)
        if not categories:
            raise ValueError("No categories found")

        self._ics_params = {
            "abfk_calendar_download": "1",
            "calendar[tourId]": str(tour_id),
            "calendar[gemeinde]": "Luzern",
            "calendar[format]": "ics",
            **{
                f"calendar[{category}]": category
                for category in str(categories).split(",")
            },
        }

    def fetch(self) -> list[Collection]:
        fresh = False
        if not self._ics_params:
            fresh = True
            self.fetch_ics_params()

        try:
            entries = self.get_collections()
            if not entries:
                raise ValueError("No entries found")
            return entries
        except Exception as e:
            if fresh:
                raise e
            self.fetch_ics_params()
            return self.get_collections()

    def get_collections(self) -> list[Collection]:
        if not self._ics_params:
            raise ValueError("No ics params found")

        r = requests.get(API_URL, params=self._ics_params)
        r.raise_for_status()
        data = self._ics.convert(r.text)

        # extract entries
        entries = []

        for date, waste_type in data:
            # New fetcher uses different names this should prevent breaking changes
            waste_type = OLD_WASTE_NAME.get(waste_type, waste_type)
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
