import logging
import re
import typing
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
)

TITLE = "Town of Cambridge (WA)"
DESCRIPTION = "Source for Town of Cambridge (Western Australia) rubbish collection."
URL = "https://www.cambridge.wa.gov.au"
TEST_CASES = {
    "Geolocation ID": {"geolocation_id": "ec16b372-7aab-4082-8519-2163c431777d"},
    "Cambridge Library": {"street_address": "99 The Boulevard, FLOREAT 6014"},
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "general waste": Icons.GENERAL_WASTE,
    "green waste": Icons.GARDEN,
    "fogo": Icons.ORGANIC,
    "recycling": Icons.RECYCLING,
}


class SourceConfigurationError(ValueError):
    pass


class SourceParseError(ValueError):
    pass


class Source:
    OC_GEOLOCATION_SEARCH_URL = "https://www.cambridge.wa.gov.au/api/v1/myarea/search"

    OC_SESSION_URL = (
        "https://www.cambridge.wa.gov.au/Residents/Waste-Recycling/Find-My-Bin-Day"
    )
    OC_CALENDAR_URL = (
        "https://www.cambridge.wa.gov.au/ocapi/Public/myarea/wasteservices"
    )

    OC_RE_DATE_STR = re.compile(r"[^\s]+\s(\d{1,2}/\d{1,2}/\d{4})")

    def __init__(
        self,
        street_address: typing.Optional[str] = None,
        geolocation_id: typing.Optional[str] = None,
    ):
        if street_address is None and geolocation_id is None:
            raise SourceArgumentExceptionMultiple(
                ["street_address", "geolocation_id"],
                "Either street_address or geolocation_id must have a value",
            )

        self._street_address = street_address
        self._geolocation_id = geolocation_id

    def fetch(self) -> typing.List[Collection]:
        # Use curl_cffi session to bypass Incapsula bot protection
        session = requests.Session(impersonate="chrome")

        geolocation_id = self._geolocation_id
        if geolocation_id is None:
            # Search for geolocation ID
            geolocation_response = session.get(
                self.OC_GEOLOCATION_SEARCH_URL,
                params={"keywords": self._street_address, "maxresults": 1},
                headers={"Accept": "application/json"},
            )
            geolocation_response.raise_for_status()

            # Pull ID from results
            geolocation_result = geolocation_response.json()
            _LOGGER.debug(f"Search response: {geolocation_response!r}")

            if "success" in geolocation_result and not geolocation_result["success"]:
                raise SourceParseError(
                    "Unspecified server-side error when searching address"
                )

            if (
                "Items" not in geolocation_result
                or geolocation_result["Items"] is None
                or len(geolocation_result["Items"]) < 1
            ):
                raise SourceParseError(
                    "Expected list of locations from address search, got empty or missing list"
                )

            geolocation_data = geolocation_result["Items"][0]

            if "Id" not in geolocation_data:
                raise SourceParseError(
                    "Location in address search result but missing geolocation ID"
                )

            geolocation_id = geolocation_data["Id"]
            _LOGGER.info(
                f"Address {self._street_address} mapped to geolocation ID {geolocation_id}"
            )

        calendar_request = session.get(self.OC_SESSION_URL)
        calendar_request.raise_for_status()

        calendar_request = session.get(
            self.OC_CALENDAR_URL,
            params={"geolocationid": geolocation_id, "ocsvclang": "en-AU"},
        )
        calendar_request.raise_for_status()

        calendar_result = calendar_request.json()
        _LOGGER.debug(f"Calendar response: {calendar_result!r}")

        if "success" in calendar_result and not calendar_result["success"]:
            raise SourceParseError(
                "Unspecified server-side error when getting calendar"
            )

        # Extract entries from bundled HTML
        calendar_parser = BeautifulSoup(
            calendar_result["responseContent"], "html.parser"
        )

        pickup_entries = []

        for element in calendar_parser.find_all("article"):
            _LOGGER.debug(f"Parsing collection: {element!r}")

            waste_type = element.h3.string

            # Extract and parse collection date
            waste_date_match = self.OC_RE_DATE_STR.match(
                element.find(class_="next-service").string.strip()
            )

            if waste_date_match is None:
                continue

            waste_date = datetime.strptime(waste_date_match[1], "%d/%m/%Y").date()

            # Base icon on type
            waste_icon = ICON_MAP.get(waste_type.lower())

            pickup_entries.append(Collection(waste_date, waste_type, waste_icon))
            _LOGGER.info(
                f"Collection for {waste_type} (icon: {waste_icon}) on {waste_date}"
            )

        return pickup_entries
