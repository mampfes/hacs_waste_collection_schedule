from datetime import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Medway Council"
DESCRIPTION = "Source for medway.gov.uk services for Medway Council"
URL = "https://www.medway.gov.uk"

TEST_CASES = {
    "known_uprn": {"uprn": "100062390963"},
    "known_uprn_as_number": {"uprn": 100062390963},
    "by_postcode": {"postcode": "ME4 4AY", "house_name_or_number": "194-198"},
}

ICON_MAP = {
    "Waste Collection": "mdi:trash-can",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your UPRN by entering your postcode at https://www.medway.gov.uk/homepage/45/check_collection_day. Alternatively provide your postcode and house name/number.",
}


API_BASE = "https://api.medway.gov.uk/api"
HEADERS = {
    "Origin": "https://www.medway.gov.uk",
    "Referer": "https://www.medway.gov.uk/",
}
TIMEOUT = 30


class Source:
    def __init__(self, uprn=None, postcode=None, house_name_or_number=None):
        self._uprn = str(uprn).strip() if uprn is not None else None
        self._postcode = str(postcode).strip() if postcode is not None else None
        self._housenameornumber = (
            str(house_name_or_number).strip()
            if house_name_or_number is not None
            else None
        )

        if not any((self._uprn, self._postcode and self._housenameornumber)):
            errors = []
            if self._postcode:
                errors.append("house_name_or_number")
            elif self._housenameornumber:
                errors.append("postcode")
            else:
                errors = ["uprn", "postcode", "house_name_or_number"]
            raise SourceArgumentExceptionMultiple(
                errors,
                "Must provide either a UPRN or both the Postcode and House Name or Number",
            )

    def fetch(self) -> list[Collection]:
        if self._uprn is None:
            self._uprn = self._get_uprn()

        resp = requests.get(
            f"{API_BASE}/waste/getwasteday/{self._uprn}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        collection_date = datetime.fromisoformat(data["nextCollection"]).date()

        return [
            Collection(
                date=collection_date,
                t="Waste Collection",
                icon=ICON_MAP["Waste Collection"],
            )
        ]

    def _get_uprn(self) -> str:
        postcode = self._postcode.replace(" ", "").lower()
        resp = requests.get(
            f"{API_BASE}/addressing/getaddresses/{postcode}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        addresses = resp.json()

        if not addresses:
            raise SourceArgumentNotFound("postcode", self._postcode)

        for addr in addresses:
            paon = addr.get("paon", "").lower()
            saon = addr.get("saon", "").lower()
            search = self._housenameornumber.lower()
            if search == paon or search == saon:
                return str(addr["uprn"])

        raise SourceArgumentNotFoundWithSuggestions(
            "house_name_or_number",
            self._housenameornumber,
            [a["addressText"] for a in addresses],
        )
