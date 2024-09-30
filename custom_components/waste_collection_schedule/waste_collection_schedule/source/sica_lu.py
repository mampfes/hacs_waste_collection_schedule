import datetime
from typing import TypedDict

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "SICA"
DESCRIPTION = "Source script for sica.lu served municipalities"
URL = "https://sica.lu"
TEST_CASES = {
    "Habscht": {"municipality": "habscht"},
    "Steinfort": {"municipality": "Steinfort"},
}

BASE_URL = "https://dashboard.sicaapp.lu"
API_URL = f"{BASE_URL}/api/api/app"
HEADERS = {"User-Agent": "SicaAPP", "Accept": "application/json"}
ICON_MAP = {
    "Residual waste": "mdi:trash-can",
    "Valorlux - blue bag": "mdi:recycle",
    "Organic waste": "mdi:leaf",
    "Glass": "mdi:bottle-wine-outline",
    "Paper /Carton": "mdi:newspaper",
    "Scrap and electrical appliances": "mdi:washing-machine",
    "Clothing and Shoes": "mdi:tshirt-crew",
    "Hedges, Shrubs and Trees": "mdi:tree",
    "Bulky waste": "mdi:sofa",
}


class LanguageDict(TypedDict):
    en: str
    fr: str
    de: str
    lb: str


class MunicipalityData(TypedDict):
    id: int
    name: LanguageDict
    feeData: list[dict[str, LanguageDict]]
    isDisabled: bool
    parentCommunity_id: int | None
    children: list["MunicipalityData"]


class MunicipalitiesResult(TypedDict):
    data: list[MunicipalityData]


class PickupType(TypedDict):
    id: int
    name: LanguageDict
    description: str | None
    collectionInfo: LanguageDict
    color: str
    isBookable: bool
    isDisabled: bool
    icon_id: int
    created_at: str
    updated_at: str
    icon: dict[str, str | None | int]


class CollectionEntry(TypedDict):
    id: int
    date: str
    note: None | str
    description: LanguageDict | None
    isDisabled: bool
    status: str
    community_id: int
    comunity_id: int
    creator_id: int
    pickupType_id: int
    created_at: str
    updated_at: str
    pickup_type: PickupType


class Source:
    def __init__(self, municipality: str) -> None:
        self._municipality = municipality.lower()
        self._municipality_id: int | None = None

    @staticmethod
    def _fetch_json(
        url: str, headers: dict
    ) -> MunicipalitiesResult | list[CollectionEntry]:
        r = requests.get(url, headers)
        if r.status_code != 200:
            r.raise_for_status()
        try:
            data = r.json()
        except ValueError as e:
            raise ValueError(f"Error decoding JSON from API: {e} - {r.text}")
        return data

    def _get_municipality_id(self) -> None:
        url = f"{API_URL}/community"
        data = self._fetch_json(url, HEADERS)
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected data type: {type(data)}")
        _municipalities: dict[str, int] = {}
        _municipalities.update(
            {
                item["name"]["en"].lower(): item["id"]
                for m in data.get("data", [])
                for item in [m] + m.get("children", [])
                if not item["isDisabled"] and not item.get("children", [])
            }
        )
        self._municipality_id = _municipalities.get(self._municipality)
        if not self._municipality_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, list(_municipalities.keys())
            )

    def fetch(self) -> list[Collection]:
        if not self._municipality_id:
            self._get_municipality_id()

        url = f"{API_URL}/pickup-date"
        data = self._fetch_json(url, HEADERS)
        if not isinstance(data, list):
            raise ValueError(f"Unexpected data type: {type(data)}")
        entries = [
            Collection(
                date=datetime.date.fromisoformat(e["date"].split(" ")[0]),
                t=e["pickup_type"]["name"]["en"],
                picture=f"{BASE_URL}{e['pickup_type']['icon']['url']}",
                icon=ICON_MAP.get(e["pickup_type"]["name"]["en"]),
            )
            for e in data
            if not e["isDisabled"] and e["community_id"] == self._municipality_id
        ]
        return entries
