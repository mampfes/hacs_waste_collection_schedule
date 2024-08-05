import logging
import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Whitehorse City Counfil"
DESCRIPTION = "Source for Whitehorse City Counfil."
URL = "https://www.whitehorse.vic.gov.au"
TEST_CASES = {
    "17 Main Street BLACKBURN": {"address": "17 Main Street BLACKBURN"},
    "6/16 Ashted Road": {"address": "6/16 Ashted Road"},
}

ICON_MAP = {
    "Household": "mdi:trash-can",
    "GOBS": "mdi:leaf",
    "Recycle": "mdi:recycle",
}


SEARCH_URL = "https://map.whitehorse.vic.gov.au/weave/services/v1/index/search"
BIN_REQUEST_URL = (
    "https://map.whitehorse.vic.gov.au/weave/services/v1/feature/getFeaturesByIds"
)

# opening or closing tag
HTML_TAG_REGEX = re.compile(r"</?.*?>")


class Source:
    def __init__(self, address: str):
        self._address: str = address.lower().strip()
        self._address_id = None

    def _matches_address(self, address: str) -> bool:
        return self._address == re.sub(HTML_TAG_REGEX, "", address).lower().strip()

    def _fetch_address_id(self) -> None:
        args: dict[str, str | int] = {
            "start": 0,
            "limit": 1000,
            "indexes": "index.property",
            "type": "EXACT",
            "crs": "EPSG:3857",
            "query": self._address,
        }

        # get json file
        r = requests.get(SEARCH_URL, params=args)
        r.raise_for_status()

        data = r.json()

        if "results" not in data or not data["results"]:
            raise ValueError("Could not find address")

        self._address_id = None
        if len(data["results"]) == 1:
            self._address_id = data["results"][0]["id"]
        else:
            for address in data["results"]:
                if self._matches_address(address["display1"]):
                    self._address_id = address["id"]
                    break

        if not self._address_id:
            raise ValueError(
                "Could not find address, maybe try one one of the following: "
                + ", ".join(
                    [
                        re.sub(HTML_TAG_REGEX, "", address["display1"])
                        for address in data["results"]
                    ]
                )
            )

    def fetch(self) -> list[Collection]:
        """Get address ID if not set and fetch collections, tries to get address ID again if using old ID and get_collections fails."""
        fresh_id = False
        if not self._address_id:
            self._fetch_address_id()
            fresh_id = True

        try:
            return self._get_collections()
        except Exception:
            if fresh_id:
                raise
            self._fetch_address_id()
            return self._get_collections()

    def _get_house_hold_waste(self, weekday: str) -> list[Collection]:
        today = date.today()

        next_match: date | None = None
        for i in range(7):
            if (today + timedelta(days=i)).strftime("%A").lower() == weekday.lower():
                next_match = today + timedelta(days=i)
        if not next_match:
            raise ValueError("Invalid weekday")

        return [
            Collection(
                date=next_match + timedelta(weeks=i),
                t="Household",
                icon=ICON_MAP.get("Household"),
            )
            for i in range(10)
        ]

    def _get_collections(self) -> list[Collection]:
        if not self._address_id:
            raise ValueError("Address ID is not set")

        args2: dict[str, str | list[str]] = {
            "entityId": "lyr_vicmap_property",
            "datadefinition": [
                "dd_whm_property_waste",
            ],
            "ids": self._address_id,
            "outCrs": "EPSG:3857",
            "returnCentroid": "false",
        }
        r = requests.get(BIN_REQUEST_URL, params=args2)
        r.raise_for_status()
        data = r.json()
        entries = []
        for features in data["features"]:
            waste_list: dict[str, str] = features.get("properties", {}).get(
                "dd_whm_property_waste", []
            )
            if not waste_list:
                continue
            for waste_map in waste_list:
                try:
                    entries.extend(
                        self._get_house_hold_waste(waste_map.get("collectionDay", ""))
                    )
                except ValueError:
                    _LOGGER.warning(
                        "Could not get household waste for weekday '%s'",
                        waste_map.get("collectionDay", ""),
                    )
                for key, value in waste_map.items():
                    if not key.lower().startswith("next"):
                        continue
                    bin_type = key.removeprefix("next").strip()

                    try:
                        # value format like: 12 Aug 2024
                        date_ = datetime.strptime(value, "%d %b %Y").date()
                    except ValueError:
                        _LOGGER.warning("Could not parse date %s", value)
                        continue

                    icon = ICON_MAP.get(bin_type)

                    entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
