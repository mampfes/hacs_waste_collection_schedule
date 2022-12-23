import contextlib
import re
from base64 import standard_b64decode
from datetime import datetime
from typing import List, Literal, Optional, TypedDict, Union

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "C-Trace Bürgerportal"
URL = "https://www.c-trace.de"
DESCRIPTION = "Source for waste collection in multiple service areas."
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
ICONS = {
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
# Important: Remove the trailing slash
OPERATOR_URLS: dict[Operator, str] = {
    "cochem_zell": "https://buerger-portal-cochemzell.azurewebsites.net",
    "alb_donau": "https://buerger-portal-albdonaukreisabfallwirtschaft.azurewebsites.net",
    "biedenkopf": "https://biedenkopfmzv.buergerportal.digital",
}


def quote_none(value: Optional[str]) -> str:
    if value is None:
        return "null"

    return f"'{value}'"


class Source:
    def __init__(
        self,
        operator: Operator,
        district: str,
        street: str,
        subdistrict: Optional[str] = None,
        number: Union[int, str, None] = None,
    ):
        self.api_url = f"{OPERATOR_URLS[operator]}/api"
        self.district = district
        self.subdistrict = subdistrict
        self.street = street
        self.number = number

    def fetch(self):
        session = requests.session()
        session.headers.update(API_HEADERS)

        year = datetime.now().year
        entries: list[Collection] = []

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
                date = datetime.utcfromtimestamp(timestamp / 1000).date()
                waste_type = collection["Abfuhrplan"]["GefaesstarifArt"]["Abfallart"][
                    "Name"
                ]
                icon = None
                # Maybe append collection["Abfuhrplan"]["GefaesstarifArt"]["Volumen"]["VolumenWert"] to waste type

                for icon_type, tested_icon in ICONS.items():
                    if icon_type.lower() in waste_type.lower():
                        icon = tested_icon

                entries.append(Collection(date, waste_type, icon or "mdi:trash-can"))

        if len(entries) == 0:
            raise ValueError(
                "No collections found! Please verify that your configuration is correct."
            )

        return entries

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
