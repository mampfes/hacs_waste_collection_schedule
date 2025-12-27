from __future__ import annotations

import logging
from datetime import date
from typing import Literal

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

_LOGGER = logging.getLogger(__name__)

TITLE = "Afvalstoffendienst.nl"
DESCRIPTION = (
    "Source for 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze"
)
URL = "https://www.afvalstoffendienst.nl/"


TEST_CASES = {
    "s-hertogenbosch, 5151MS 37 ": {
        "postcode": "5151MS",
        "house_number": 37,
    },
    "heuden, 5256EJ, 44C": {
        "postcode": "5256EJ",
        "house_number": 44,
        "addition": "C",
    },
    "vught, 5262 CJ 18": {
        "postcode": "5262 CJ",
        "house_number": "18",
    },
    "Oisterwijk 5062 ER 13": {
        "postcode": "5062 ER",
        "house_number": "13",
    },
    "Altena 4286 AL 1": {
        "postcode": "4286 AA",
        "house_number": "1",
    },
    "bernheze": {"postcode": "5473 EW", "house_number": 50},
}

EXTRA_INFO = [{"title": TITLE, "url": URL}]

REGIONS_LITERAL = Literal[
    "heusden",
    "vught",
    "oisterwijk",
    "altena",
    "bernheze",
    "s-hertogenbosch",
    "afvalstoffendienst",
]

ICON_MAP = {
    "Groente-Fruit-Tuinafval-etensresten": "mdi:apple",
    "Plastic-Blik-Drankkartons": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Restafval": "mdi:trash-can",
    "Glas": "mdi:glass-fragile",
    "Kerstboom": "mdi:pine-tree",
}

API_URL = "https://www.afvalstoffendienst.nl"


class Source:
    def __init__(
        self,
        postcode: str,
        house_number: str | int,
        addition: str | None = None,
        region: REGIONS_LITERAL | None = None,
    ):
        self._postcode: str = postcode.replace(" ", "").upper()
        self._house_number: str | int = house_number
        self._addition: str | None = addition.lower() if addition else None

        if region:
            region_key = region.lower()
            if region_key not in REGIONS_LITERAL.__args__:
                raise SourceArgumentNotFoundWithSuggestions(
                    f"Invalid region: {region}, must be one of {REGIONS_LITERAL.__args__}",
                    suggestions=REGIONS_LITERAL.__args__,
                )

    def _find_bag_id(self) -> str:
        url = f"{API_URL}/adressen/{self._postcode}:{self._house_number}"
        response = requests.get(url)
        response.raise_for_status()
        addresses = response.json()

        if len(addresses) == 0:
            raise Exception("no data found for this address")

        if self._addition:
            for address in addresses:
                huisletter = address.get("huisletter", "")
                toevoeging = address.get("toevoeging", "")
                if self._addition in (huisletter.lower(), toevoeging.lower()):
                    return address["bagid"]

        return addresses[0]["bagid"]

    def _fetch_flows(self, bag_id: str) -> dict[int, dict]:
        response = requests.get(f"{API_URL}/rest/adressen/{bag_id}/afvalstromen")
        response.raise_for_status()
        return {flow["id"]: flow for flow in response.json()}

    def _fetch_calendar(self, bag_id: str) -> list[dict]:
        year = date.today().year
        entries: list[dict] = []
        for target_year in (year, year + 1):
            response = requests.get(
                f"{API_URL}/rest/adressen/{bag_id}/kalender/{target_year}"
            )
            response.raise_for_status()
            entries.extend(response.json())
        return entries

    def fetch(self) -> list[Collection]:
        bag_id = self._find_bag_id()
        flows = self._fetch_flows(bag_id)
        calendar = self._fetch_calendar(bag_id)

        entries = []
        for item in calendar:
            flow = flows.get(item["afvalstroom_id"], {})
            icon_key = flow.get("icon")
            icon = ICON_MAP.get(icon_key) if icon_key else None
            entries.append(
                Collection(
                    date=date.fromisoformat(item["ophaaldatum"]),
                    t=flow.get("title", "Afval"),
                    icon=icon,
                )
            )

        return entries
