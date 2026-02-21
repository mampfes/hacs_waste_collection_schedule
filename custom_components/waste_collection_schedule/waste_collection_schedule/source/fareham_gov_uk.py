import re
from datetime import date
from typing import Iterable

import requests
from dateutil.parser import parse as date_parse
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Fareham Borough Council"
DESCRIPTION = "Source for fareham.gov.uk"
URL = "https://www.fareham.gov.uk"
TEST_CASES = {
    "HUNTS_POND_ROAD": {"road_name": "Hunts pond road", "postcode": "PO14 4PL"},
    "CHRUCH_ROAD": {"road_name": "Church road", "postcode": "SO31 6LW"},
    "BRIDGE_ROAD": {"road_name": "Bridge road", "postcode": "SO31 7GD"},
    "SEGENSWORTH_ROAD": {"road_name": "203 Segensworth road", "postcode": "PO15 5EL"},
}

API_URL = "https://www.fareham.gov.uk/internetlookups/search_data.aspx"
API_LIST = "DomesticBinCollections2025on"
DEFAULT_ICON = "mdi:trash-can"
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}


class Source:
    def __init__(self, road_name: str, postcode: str):
        if not road_name or not road_name.strip():
            raise SourceArgumentRequired(
                "road_name", "please provide the road name as listed by the council"
            )
        if not postcode or not postcode.strip():
            raise SourceArgumentRequired(
                "postcode", "please provide the postcode recognised by the council"
            )

        self._road_name = road_name.strip()
        self._postcode = postcode.strip()

    def fetch(self) -> list[Collection]:
        rows = self._request_rows(self._postcode)
        if not rows:
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "please verify the postcode on recent council correspondence",
            )

        matches = self._filter_rows(rows)

        if not matches:
            raise SourceArgumentNotFound(
                "road_name",
                self._road_name,
                "please ensure it matches the selected postcode",
            )

        collections = []
        seen = set()
        for row in matches:
            bin_info = row.get("BinCollectionInformation", "")
            for collection in self.extract_collections(bin_info):
                key = (collection.date, collection.type)
                if key in seen:
                    continue
                seen.add(key)
                collections.append(collection)

            garden_info = row.get("GardenWasteBinDay<br/>(seenotesabove)")
            if garden_info:
                for collection in self.extract_garden_collection(garden_info):
                    key = (collection.date, collection.type)
                    if key in seen:
                        continue
                    seen.add(key)
                    collections.append(collection)

        return sorted(collections, key=lambda col: col.date)

    def _request_rows(self, query: str):
        if not query:
            raise SourceArgumentRequired(
                "postcode", "please provide the postcode recognised by the council"
            )
        params = {
            "type": "JSON",
            "list": API_LIST,
            "Road or Postcode": query,
        }
        headers = {
            "user-agent": "Mozilla/5.0",
        }
        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", {}).get("rows", [])

    def _filter_rows(self, rows: Iterable[dict]):
        postcode_norm = self._normalize(self._postcode)
        house_number, street_name = self._split_house_number(self._road_name)
        street_tokens = set(self._tokenize(street_name))
        matches = []

        for row in rows:
            address = row.get("Address", "")
            address_norm = self._normalize(address)
            address_tokens = set(self._tokenize(address))

            if postcode_norm and postcode_norm not in address_norm:
                continue

            if street_tokens and not street_tokens.issubset(address_tokens):
                continue

            if house_number and house_number.lower() not in address_tokens:
                continue

            matches.append(row)

        return matches

    @staticmethod
    def _normalize(value: str):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    @staticmethod
    def _tokenize(value: str):
        if not value:
            return []
        return re.findall(r"[a-z0-9]+", value.lower())

    @staticmethod
    def _split_house_number(value: str):
        match = re.match(r"\s*(\d+[a-zA-Z]?)\s+(.+)", value)
        if match:
            return match.group(1), match.group(2).strip()
        return None, value.strip()

    def extract_collections(self, string: str) -> list[Collection]:
        """Parse collection entries like '03/11/2025 (Refuse) and 10/11/2025 (Recycling)'."""
        collections: list[Collection] = []
        if not string:
            return collections
        pattern = r"(?P<date>\d{1,2}\/\d{1,2}\/\d{4}|today) \((?P<waste_type>[^)]+)\)"
        for match in re.finditer(pattern, string):
            if match.group("date") == "today":
                collection_date = date.today()
            else:
                collection_date = date_parse(match.group("date"), dayfirst=True).date()

            waste_type = match.group("waste_type")
            collections.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, DEFAULT_ICON),
                )
            )
        return collections

    def extract_garden_collection(self, string: str) -> list[Collection]:
        collections: list[Collection] = []
        if not string:
            return collections
        match = re.search(r"(?P<date>\d{1,2}\/\d{1,2}\/\d{4})", string)
        if match:
            collection_date = date_parse(match.group("date"), dayfirst=True).date()
            collections.append(
                Collection(
                    date=collection_date,
                    t="Garden Waste",
                    icon=ICON_MAP.get("Garden Waste", DEFAULT_ICON),
                )
            )
        return collections
