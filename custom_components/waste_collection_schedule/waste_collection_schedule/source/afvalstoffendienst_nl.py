from __future__ import annotations

import logging
from datetime import date

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Afvalstoffendienst.nl"
DESCRIPTION = (
    "Source for 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze"
)
URL = "https://www.afvalstoffendienst.nl/"


TEST_CASES = {
    "s-Hertogenbosch, 5212SB 41A": {
        "postcode": "5212SB",
        "house_number": "41",
        "addition": "A",
    },
    "Heusden, 5256EJ, 32": {
        "postcode": "5256EJ",
        "house_number": "32",
    },
    "Vught, 5262TH 23": {
        "postcode": "5262TH",
        "house_number": "23",
    },
    "Cromvoirt 5266AD 31": {
        "postcode": "5266AH",
        "house_number": "102",
        "addition": "A",
    },
    "Rosmalen 5241AV 18": {
        "postcode": "5241AV",
        "house_number": "18",
    },
    "Heeswijk-Dinther 5473AB 13": {
        "postcode": "5473 AB",
        "house_number": "13",
    },
}

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
        region: str | None = None,
    ):
        self._postcode: str = postcode.replace(" ", "").upper()
        self._house_number: str | int = house_number
        self._addition: str | None = addition.lower() if addition else None
        if region is not None:
            _LOGGER.debug("region argument is ignored; API no longer uses it")

    def _find_bag_id(self) -> str:
        url = f"{API_URL}/adressen/{self._postcode}:{self._house_number}"
        response = requests.get(url)
        response.raise_for_status()
        addresses = response.json()

        if len(addresses) == 0:
            raise Exception("Address is not within service area. Please check.")

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
