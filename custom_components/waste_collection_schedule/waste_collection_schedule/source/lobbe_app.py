from datetime import datetime
from typing import Literal

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Lobbe App"
DESCRIPTION = "Source for Lobbe App."
URL = "https://lobbe.app/"
TEST_CASES = {
    "Hessen Diemelsee Am Breuschelt": {
        "state": "Hessen",
        "city": "Diemelsee",
        "street": "Am Breuschelt",
    },
    "Nordrhein-Westfalen Meschede Alte Henne": {
        "state": "Nordrhein-Westfalen",
        "city": "Meschede",
        "street": "Alte Henne",
    },
    "Nordrhein-Westfalen Willebadessen Ächternstraße": {
        "state": "Nordrhein-Westfalen",
        "city": "Willebadessen",
        "street": "Ächternstraße",
    },
}


ICON_MAP = {
    "restabfall": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "bioabfall": "mdi:leaf",
    "altpapier": "mdi:package-variant",
    "gelber": "mdi:recycle",
    "elektroschrott": "mdi:power-plug",
}

STATES = Literal["Hessen", "Nordrhein-Westfalen"]


API_URL = "https://lobbe.app/wp-admin/admin-ajax.php"
TYPES = {"gelber", "biobfall", "restabfall", "altpapier", "additional_types"}


def make_comparable(s: str) -> str:
    return (
        s.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("str.", "straße")
        .replace("ß", "ss")
        .replace(".", "")
        .replace(",", "")
    )


COUNTRY = "de"

PLACES = {
    "Hessen": [
        "Allendorf",
        "Bad Arolsen",
        "Battenberg",
        "Bromskirchen",
        "Burgwald",
        "Diemelsee",
        "Diemelstadt",
        "Edertal",
        "Frankenau",
        "Hatzfeld",
        "Korbach",
        "Lichtenfels",
        "Rosenthal",
        "Twistetal",
        "Vöhl",
        "Willingen",
    ],
    "Nordrhein-Westfalen": [
        "Altena",
        "Altenbeken",
        "Arnsberg",
        "Bad Berleburg",
        "Bad Driburg",
        "Bad Wünnenberg",
        "Balve",
        "Bestwig",
        "Borchen",
        "Borgentreich",
        "Brakel",
        "Breckerfeld",
        "Brilon",
        "Büren",
        "Delbrück",
        "Eslohe",
        "Hallenberg",
        "Halver",
        "Hemer",
        "Iserlohn",
        "Kierspe",
        "Lichtenau",
        "Marienmünster",
        "Marsberg",
        "Medebach",
        "Meinerzhagen",
        "Menden",
        "Meschede",
        "Nachrodt-Wiblingwerde",
        "Olsberg",
        "Plettenberg",
        "Rüthen",
        "Schalksmühle",
        # "Schmallenberg", # Listed but is not the current service provider
        "Steinheim",
        "Sundern",
        "Warburg",
        "Warstein",
        "Werdohl",
        "Willebadessen",
        "Winterberg",
    ],
}


EXTRA_INFO = [
    {
        "title": city,
        "default_params": {"state": state, "city": city},
    }
    for state, cities in PLACES.items()
    for city in cities
]


class Source:
    def __init__(self, state: STATES, city: str, street: str):
        self._state: str = state
        self._city: str = city
        self._street: str = street
        self._ics = ICS()

        self._state_id: int | None = None
        self._state_name: str | None = None
        self._city_id: int | None = None
        self._city_name: str | None = None
        self._street_id: int | None = None
        self._street_name: str | None = None

    @staticmethod
    def _get_id(
        action: str, compare_to: str, param_name: str, params: dict[str, str | int] = {}
    ) -> tuple[int, str]:
        params = {"action": action, **params}
        original_compare_to = compare_to
        compare_to = make_comparable(compare_to)
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()
        for d in data:
            if make_comparable(d["text"]) == compare_to:
                return d["id"], d["text"]

        raise SourceArgumentNotFoundWithSuggestions(
            param_name,
            original_compare_to,
            [d["text"] for d in data],
        )

    def _get_ids(self) -> None:
        self._state_id, self._state_name = self._get_id("state", self._state, "state")
        self._city_id, self._city_name = self._get_id(
            "place", self._city, "city", {"id": self._state_id}
        )
        self._street_id, self._street_name = self._get_id(
            "street", self._street, "street", {"id": self._city_id}
        )

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        entries = self._fetch_year(now.year)
        if now.month != 12:
            return entries
        try:
            return entries + self._fetch_year(now.year + 1)
        except Exception:
            return entries

    def _fetch_year(self, year: int) -> list[Collection]:
        fresh_id = False
        if self._street_id is None:
            self._get_ids()
            fresh_id = True
        try:
            return self._get_collections(year)
        except Exception:
            if fresh_id:
                raise
            self._get_ids()
            return self._get_collections(year)

    def _get_collections(self, year: int) -> list[Collection]:
        params = {
            "year[id]": 1,
            "year[text]": year,
            "state[id]": self._state_id,
            "state[text]": self._state_name,
            "place[id]": self._city_id,
            "place[text]": self._city_name,
            "street[id]": self._street_id,
            "street[text]": self._street_name,
            **{t: 1 for t in TYPES},
            "hours": 18,
            "minutes": 00,
            "action": "create_ical",
        }
        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        ics_url = r.json()["url"]

        r = requests.get(ics_url)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(
                Collection(d[0], d[1], ICON_MAP.get(d[1].split()[0].lower()))
            )
        return entries


def _print_extra_info() -> None:
    params = {
        "action": "state",
    }
    r = requests.get(API_URL, params=params)
    r.raise_for_status()

    places: dict[str, list[str]] = {}

    for state in r.json():
        params = {"action": "place", "id": state["id"]}
        if state["text"] not in places:
            places[state["text"]] = []

        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        for place in r.json():
            places[state["text"]].append(place["text"])

    print(places, len(places))


if __name__ == "__main__":
    _print_extra_info()
