from __future__ import annotations

import datetime
from inspect import Parameter, Signature
from typing import Any

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "KAW Mainz und Mainz-Bingen AöR"
DESCRIPTION = "Source for KAW Mainz und Mainz-Bingen AöR."
URL = "https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender"
TEST_CASES = {
    "Stadt Ingelheim Ingelheim Süd": {
        "bezirk": "Stadt Ingelheim",
        "ort": "Ingelheim Süd",
    },
    "Verbandsgemeinde Rhein-Selz, Mommenheim": {
        "bezirk": "Verbandsgemeinde Rhein-Selz",
        "ort": "mOmMenHeiM",
    },
    "Stadt Bingen, Bingen-Stadt": {
        "bezirk": "Stadt Bingen",
        "ort": "Bingen-Stadt",
    },
}


ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Glass": Icons.GLASS,
    "Biomüll": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Papiertonne": Icons.PAPER,
    "Gelbe/r Tonne / Sack": Icons.RECYCLING,
    "Gelbe Tonne": Icons.RECYCLING,
    "Problemmüll": Icons.HAZARDOUS,
    "Problemmüllbus": Icons.HAZARDOUS,
}


API_URL = "https://abfallkalender-api-lk.kaw-mainz-bingen.de/public/frontend"
RECORDS_PER_PAGE = 999999
DATE_FORMAT = "%Y-%m-%d"


class Source:
    def __init__(self, bezirk: str, ort: str, strasse: str | None = None):
        self._bezirk: str = bezirk
        self._ort: str = ort
        # Kept for compatibility with existing configurations. The new KAW API
        # exposes the public calendar by district and city only.
        self._strasse: str | None = strasse

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        settings = self._get_settings(session)
        bezirk = self._find_bezirk(settings)
        ort = self._find_ort(settings, bezirk["Id"])

        today = datetime.date.today()
        date_to = datetime.date(today.year + 1, 12, 31)

        params = {
            "Filter.SearchTerm": "",
            "Filter.DistrictId": bezirk["Id"],
            "Filter.CityId": ort["Id"],
            "Filter.StreetId": 0,
            "Filter.DateFrom": today.strftime(DATE_FORMAT),
            "Filter.DateTo": date_to.strftime(DATE_FORMAT),
            "Filter.WasteTypeIds": ",".join(
                str(waste_type["Id"])
                for waste_type in _active_items(settings["WasteTypes"])
            ),
            "Filter.ShowGroupedResults": "false",
            "Filter.RecordsPerPage": RECORDS_PER_PAGE,
            "Filter.CurrentPage": 1,
            "Filter.SortColumn": "Date",
        }

        r = session.get(f"{API_URL}/collectiondates", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        self._raise_for_api_error(data)

        entries: list[Collection] = []
        for item in data.get("DataList", []):
            date = datetime.datetime.strptime(item["Date"], "%d.%m.%Y").date()
            bin_type = item["WasteTypeName"]
            entries.append(
                Collection(
                    date,
                    bin_type,
                    ICON_MAP.get(bin_type),
                    location=item.get("Location"),
                    description=item.get("AdditionalDescription"),
                )
            )

        return entries

    def _get_settings(self, session: requests.Session) -> dict[str, Any]:
        r = session.get(
            f"{API_URL}/settings",
            params={"Filter.IncludeStaticObjects": "true"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self._raise_for_api_error(data)
        return data["Data"]

    def _find_bezirk(self, settings: dict[str, Any]) -> dict[str, Any]:
        districts = _active_items(settings["Districts"])
        district = _find_by_name(districts, self._bezirk)
        if district is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "bezirk", self._bezirk, _names(districts)
            )
        return district

    def _find_ort(self, settings: dict[str, Any], bezirk_id: int) -> dict[str, Any]:
        cities = [
            city
            for city in _active_items(settings["Cities"])
            if city["DistrictId"] == bezirk_id
        ]
        city = _find_by_name(cities, self._ort)
        if city is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "ort", self._ort, _names(cities)
            )
        return city

    @staticmethod
    def _raise_for_api_error(data: dict[str, Any]) -> None:
        if data.get("ReturnCode") not in (0, 990):
            raise Exception(
                data.get("ErrorMessage")
                or data.get("Message")
                or "Invalid response from server"
            )


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _active_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item for item in items if item.get("Id", 0) > 0 and item.get("RecordState") == 1
    ]


def _find_by_name(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    normalized_name = _normalize(name)
    return next(
        (item for item in items if _normalize(item.get("Name", "")) == normalized_name),
        None,
    )


def _names(items: list[dict[str, Any]]) -> list[str]:
    return [item["Name"] for item in items]


Source.__init__.__signature__ = Signature(
    parameters=[
        Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),
        Parameter("bezirk", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter("ort", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
    ]
)
