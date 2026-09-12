import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.source.impactapps_com_au import (
    Source as ImpactAppsSource,  # type: ignore[attr-defined]
)

TITLE = "Hobsons Bay City Council"
DESCRIPTION = "Source for Hobsons Bay City Council waste & recycling collection"
URL = "https://www.hobsonsbay.vic.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Civic Parade Medical Centre": {"street_address": "399 Queen St, Altona Meadows"},
    "Hecho En Mexico Altona": {"street_address": "48 Pier St, Altona"},
    "Williamstown, no comma": {"street_address": "20 Merrett Dr Williamstown"},
}
PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street address",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street number, street name and suburb as shown on the council's bin collection calendar, for example '399 Queen St, Altona Meadows'. The comma is optional.",
    }
}

# Hobsons Bay moved its collection lookup to Impact Apps (waste-info.com.au);
# the previous Algolia address index rejects the shipped credentials with a 403.
SERVICE = "hobsons-bay"
API_URL = f"https://{SERVICE}.waste-info.com.au"
HEADERS = {"user-agent": "Mozilla/5.0"}

_LOGGER = logging.getLogger(__name__)


def _normalise(value: str) -> str:
    return " ".join(value.replace(",", " ").split()).casefold()


def split_address(street_address: str, suburbs: list[str]) -> tuple[str, str, str]:
    """Split "<number> <street>[,] <suburb>" into number, street and suburb.

    The suburb is matched against the suburbs the council actually serves, so a
    multi-word suburb ("Altona Meadows") is not mistaken for part of the street
    and the comma stays optional.
    """
    cleaned = " ".join(street_address.replace(",", " ").split())
    matches = [s for s in suburbs if _normalise(cleaned).endswith(f" {_normalise(s)}")]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_address", street_address, sorted(suburbs)
        )

    # longest match wins, so "Altona Meadows" is preferred over "Altona"
    suburb = max(matches, key=len)
    number, _, street = cleaned[: -len(suburb)].strip().partition(" ")
    if not number or not street:
        raise SourceArgumentException(
            "street_address",
            f"Could not read a house number and street from '{street_address}'. "
            "Expected '<number> <street>, <suburb>', e.g. '399 Queen St, Altona Meadows'",
        )
    return number, street, suburb


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def _get(self, session: requests.Session, path: str, params: dict | None = None):
        response = session.get(f"{API_URL}/api/v1/{path}", params=params)
        response.raise_for_status()
        return response.json()

    def _find_id(self, value: str, items: list[dict]) -> int:
        wanted = _normalise(value)
        for item in items:
            if _normalise(item["name"]) == wanted:
                return item["id"]
        raise SourceArgumentNotFoundWithSuggestions(
            "street_address", value, [item["name"] for item in items]
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        suburbs = self._get(session, "localities.json")["localities"]
        number, street, suburb = split_address(
            self._street_address, [s["name"] for s in suburbs]
        )
        _LOGGER.debug(
            "Resolved %s to %s / %s / %s", self._street_address, number, street, suburb
        )

        suburb_id = self._find_id(suburb, suburbs)
        streets = self._get(session, "streets.json", {"locality": suburb_id})["streets"]
        street_id = self._find_id(street, streets)

        properties = self._get(session, "properties.json", {"street": street_id})[
            "properties"
        ]
        property_id = next(
            (
                p["id"]
                for p in properties
                if _normalise(p["name"].partition(" ")[0]) == _normalise(number)
            ),
            None,
        )
        if property_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_address",
                self._street_address,
                [p["name"] for p in properties],
            )

        # Impact Apps owns the event parsing, icons and recurring-event expansion
        return ImpactAppsSource(service=SERVICE, property_id=property_id).fetch()
