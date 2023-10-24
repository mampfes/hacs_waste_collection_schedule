import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Warsaw"
DESCRIPTION = "Source for Warsaw city garbage collection"
URL = "https://warszawa19115.pl"
TEST_CASES = {
    "Street Name": {"street_address": "MARSZAŁKOWSKA 84/92, 00-514 Śródmieście"},
    "Geolocation ID": {"geolocation_id": "3830963"},
}

_LOGGER = logging.getLogger(__name__)


class SourceConfigurationError(ValueError):
    pass


class SourceParseError(ValueError):
    pass


OC_URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow"
OC_PARAMS = {
    "p_p_id": "portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ",
    "p_p_lifecycle": "2",
    "p_p_resource_id": "ajaxResource",
}
OC_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}
NAME_MAP = {
    "BG": "Bio restauracyjne",
    "BK": "Bio",
    "MT": "Metale i tworzywa sztuczne",
    "OP": "Papier",
    "OS": "Szkło",
    "OZ": "Zielone",
    "WG": "Odpady wielkogabarytowe",
    "ZM": "Odpady zmieszane",
}


class Source:
    def __init__(self, street_address=None, geolocation_id=None):
        if street_address is None and geolocation_id is None:
            raise SourceConfigurationError(
                "Either street_address or geolocation_id must have a value"
            )
        self._street_address = street_address
        self._geolocation_id = geolocation_id

    def get_geolocation_id(self, street_address) -> str:
        geolocation_session = requests.Session()
        geolocation_request = geolocation_session.get(OC_URL)
        geolocation_request.raise_for_status()

        # Geolocation call requires 'autocompleteResourceURL' param to work
        OC_PARAMS["p_p_resource_id"] = "autocompleteResource"

        # Search for geolocation ID
        OC_PARAMS[
            "_portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ_name"
        ] = street_address
        geolocation_response = geolocation_session.get(
            OC_URL,
            headers=OC_HEADERS,
            params=OC_PARAMS,
        )
        geolocation_response.raise_for_status()

        # Pull ID from results
        geolocation_result = geolocation_response.json()
        _LOGGER.debug(f"Search response: {geolocation_response!r}")

        if len(geolocation_result) < 1:
            raise SourceParseError(
                "Expected list of locations from address search, got empty or missing list"
            )

        geolocation_data = geolocation_result[0]

        if "addressPointId" not in geolocation_data:
            raise SourceParseError(
                "Location in address search result but missing geolocation ID"
            )

        geolocation_id = geolocation_data["addressPointId"]
        _LOGGER.info(
            f"Address {street_address} mapped to geolocation ID {geolocation_id}"
        )

        return geolocation_id

    def fetch(self):
        # When only an address is specified, get geolocation on first fetch
        if self._geolocation_id is None:
            self._geolocation_id = self.get_geolocation_id(self._street_address)

        # Calendar lookup cares about a cookie, so a Session must be used
        calendar_session = requests.Session()
        calendar_request = calendar_session.get(OC_URL)
        calendar_request.raise_for_status()

        # Calendar call requires 'ajaxResourceURL' param to work
        OC_PARAMS["p_p_resource_id"] = "ajaxResource"

        OC_PARAMS[
            "_portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ_addressPointId"
        ] = self._geolocation_id
        calendar_request = calendar_session.get(
            OC_URL,
            headers=OC_HEADERS,
            params=OC_PARAMS,
        )
        calendar_request.raise_for_status()

        calendar_result = calendar_request.json()
        _LOGGER.debug(f"Calendar response: {calendar_result!r}")

        if (
            len(calendar_result) <= 0
            or "harmonogramy" not in calendar_result[0]
            or len(calendar_result[0]["harmonogramy"]) <= 0
        ):
            raise SourceParseError(
                "Expected list of dates from calendar search, got empty or missing list"
            )

        entries = []

        for result in calendar_result:
            for entry in result["harmonogramy"]:
                if entry["data"]:
                    original_type = entry["frakcja"]["id_frakcja"]
                    waste_type = NAME_MAP.get(original_type, original_type)
                    waste_date = datetime.strptime(entry["data"], "%Y-%m-%d").date()
                    entries.append(Collection(waste_date, waste_type))

        return entries
