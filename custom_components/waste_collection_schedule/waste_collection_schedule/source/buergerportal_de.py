import datetime
import re
from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict, Union

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bürgerportal"
URL = "https://www.c-trace.de"
DESCRIPTION = "Source for waste collection in multiple service areas."


def EXTRA_INFO():
    return [{"title": s["title"], "url": s["url"]} for s in SERVICE_MAP]


TEST_CASES = {
    "Cochem-Zell": {
        "operator": "cochem_zell",
        "district": "Bullay",
        "subdistrict": "Bullay",
        "street": "Layenweg",
        "number": 3,
    },
    "Alb-Donau": {
        "operator": "alb_donau",
        "district": "Blaubeuren",
        "street": "Alberstraße",
        "number": 3,
    },
    "Biedenkopf": {
        "operator": "biedenkopf",
        "district": "Biedenkopf",
        "subdistrict": "Breidenstein",
        "street": "Auf dem Hammer",
        "number": 1,
    },
}

ICON_MAP = {
    "mobil": "mdi:truck",
    "bio": "mdi:leaf",
    "papier": "mdi:package-variant",
    "verpackung": "mdi:recycle",
    "gelb": "mdi:recycle",
    "lvp": "mdi:recycle",
    "rest": "mdi:trash-can",
    "gruen": "mdi:forest",
    "grün": "mdi:forest",
    "baum": "mdi:forest",
    "schnitt": "mdi:forest",
    "schad": "mdi:biohazard",
}
API_HEADERS = {
    "Accept": "application/json, text/plain;q=0.5",
    "Cache-Control": "no-cache",
}
Operator = Literal["cochem_zell", "alb_donau", "biedenkopf"]

SERVICE_MAP = [
    {
        "title": "KV Cochem-Zell",
        "url": "https://www.cochem-zell-online.de/",
        "api_url": "https://buerger-portal-cochemzell.azurewebsites.net/api",
        "operator": "cochem_zell",
    },
    {
        "title": "Abfallwirtschaft Alb-Donau-Kreis",
        "url": "https://www.aw-adk.de/",
        "api_url": "https://buerger-portal-albdonaukreisabfallwirtschaft.azurewebsites.net/api",
        "operator": "alb_donau",
    },
    {
        "title": "MZV Biedenkopf",
        "url": "https://mzv-biedenkopf.de/",
        "api_url": "https://biedenkopfmzv.buergerportal.digital/api",
        "operator": "biedenkopf",
    },
    {
        "title": "Bürgerportal Bedburg",
        "url": "https://www.bedburg.de/",
        "api_url": "https://buerger-portal-bedburg.azurewebsites.net",
        "operator": "bedburg",
    },
]


# This datalcass is used for adding entries to a set and remove duplicate entries.
# The default `Collection` extends the standard dict and thus is not hashable.
@dataclass(frozen=True, eq=True)
class CollectionEntry:
    date: datetime.date
    waste_type: str
    icon: Optional[str]

    def export(self) -> Collection:
        return Collection(self.date, self.waste_type, self.icon)


def quote_none(value: Optional[str]) -> str:
    if value is None:
        return "null"

    return f"'{value}'"


def get_api_map():
    return {s["operator"]: s["api_url"] for s in SERVICE_MAP}


class Source:
    def __init__(
        self,
        operator: Operator,
        district: str,
        street: str,
        subdistrict: Optional[str] = None,
        number: Union[int, str, None] = None,
        show_volume: bool = False,
    ):
        self.api_url = get_api_map()[operator]
        self.district = district
        self.subdistrict = subdistrict
        self.street = street
        self.number = number
        self.show_volume = show_volume

    def fetch(self) -> list[Collection]:
        session = requests.session()
        session.headers.update(API_HEADERS)

        year = datetime.datetime.now().year
        entries: set[CollectionEntry] = set()

        district_id = self.fetch_district_id(session)
        street_id = self.fetch_street_id(session, district_id)
        # Eventually verify house number in the future

        params = {
            "$expand": "Abfuhrplan,Abfuhrplan/GefaesstarifArt/Abfallart,Abfuhrplan/GefaesstarifArt/Volumen",
            "$orderby": "Abfuhrplan/GefaesstarifArt/Abfallart/Name,Abfuhrplan/GefaesstarifArt/Volumen/VolumenWert",
            "orteId": district_id,
            "strassenId": street_id,
            "jahr": year,
        }

        if self.number:
            params["hausNr"] = (f"'{self.number}'",)

        res = session.get(
            f"{self.api_url}/AbfuhrtermineAbJahr",
            params=params,
        )
        res.raise_for_status()
        payload: CollectionsRes = res.json()

        date_regex = re.compile(r"\d+")

        for collection in payload["d"]:
            if date_match := re.search(date_regex, collection["Termin"]):
                timestamp = float(date_match.group())
                date = datetime.datetime.utcfromtimestamp(timestamp / 1000).date()
                waste_type = collection["Abfuhrplan"]["GefaesstarifArt"]["Abfallart"][
                    "Name"
                ]
                icon = None

                for icon_type, tested_icon in ICON_MAP.items():
                    if icon_type.lower() in waste_type.lower():
                        icon = tested_icon

                if self.show_volume:
                    volume = int(
                        collection["Abfuhrplan"]["GefaesstarifArt"]["Volumen"][
                            "VolumenWert"
                        ]
                    )
                    waste_type = f"{waste_type} ({volume} l)"

                entries.add(CollectionEntry(date, waste_type, icon))

        if len(entries) == 0:
            raise ValueError(
                "No collections found! Please verify that your configuration is correct."
            )

        return [entry.export() for entry in entries]

    def fetch_district_id(self, session: requests.Session) -> int:
        res = session.get(
            f"{self.api_url}/OrteMitOrtsteilen",
            headers=API_HEADERS,
        )
        res.raise_for_status()
        payload: DistrictsRes = res.json()

        try:
            return next(
                entry["OrteId"]
                for entry in payload["d"]
                if entry["Ortsname"] == self.district
                and entry["Ortsteilname"] == self.subdistrict
            )
        except StopIteration:
            raise ValueError(
                "District id cannot be fetched. "
                "Please make sure that you entered a subdistrict if there is a comma on the website."
            )

    def fetch_street_id(self, session: requests.Session, district_id: int):
        res = session.get(
            f"{self.api_url}/Strassen",
            params={
                "$filter": f"Ort/OrteId eq {district_id} and OrtsteilName eq {quote_none(self.subdistrict)}",
                "$orderby": "Name asc",
            },
            headers=API_HEADERS,
        )
        res.raise_for_status()
        payload: StreetsRes = res.json()

        try:
            return next(
                entry["StrassenId"]
                for entry in payload["d"]
                if entry["Name"] == self.street
            )
        except StopIteration:
            raise ValueError(
                "Street ID cannot be fetched. Please verify your configuration."
            )


# Typed dictionaries for the API
# Automatically generated using https://pytyper.dev/


class DistrictRes(TypedDict):
    OrteId: int
    Ortsname: str
    Ortsteilname: Optional[str]


class DistrictsRes(TypedDict):
    d: List[DistrictRes]


class StreetRes(TypedDict):
    StrassenId: int
    Name: str
    Plz: str


class StreetsRes(TypedDict):
    d: List[StreetRes]


class Capacity(TypedDict):
    VolumenId: int
    VolumenWert: str


class WasteType(TypedDict):
    AbfallartenId: int
    Code: str
    Name: str
    Farbe: str
    IsBio: bool
    IsPapier: bool
    IsRest: bool
    IsWertstoff: bool
    Bemerkung: None
    Aktiv: None
    IsSchadstoff: None


class ContainerType(TypedDict):
    GefaesstarifArtenId: int
    BescheidText: None
    BescheidTextLeerungsgebuehr: None
    Bezeichnung: str
    GefaesstarifArtVerwenden: bool
    GefaesstarifArtVerwendenAbfallkalender: bool
    Bemerkung: None
    Volumen: Capacity
    Abfallart: WasteType
    # Abfuhrrhythmus: Abfuhrrhythmus


class CollectionPlan(TypedDict):
    AbfuhrplaeneId: int
    Jahr: int
    GefaesstarifArt: ContainerType
    # AbfallartenObj: Abfuhrrhythmus


class CollectionRes(TypedDict):
    AbfuhrtermineId: int
    Termin: str
    Abfuhrplan: CollectionPlan


class CollectionsRes(TypedDict):
    d: List[CollectionRes]
