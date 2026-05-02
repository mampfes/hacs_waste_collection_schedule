import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

_STREET_ADDRESS_ARG_NAME = "street_address"
_LOGGER = logging.getLogger(__name__)

TITLE = "City of Glen Eira"
DESCRIPTION = "Source for the Glen Eira City Council rubbish collection."
URL = "https://www.gleneira.vic.gov.a/"
TEST_CASES = {
    # "Empty Address": {_STREET_ADDRESS_ARG_NAME: ""},
    # "Invalid Address": {_STREET_ADDRESS_ARG_NAME: "Blah blah i dont exist"},
    # "Ambiguous Address": {_STREET_ADDRESS_ARG_NAME: "55 Vi"},
    "Elsternwick Library": {
        _STREET_ADDRESS_ARG_NAME: "4 Staniland Grove ELSTERNWICK VIC 3185"
    },
}

SEARCH_PAGE_URL = "https://www.gleneira.vic.gov.au/our-city/in-your-area"
API_URL = SEARCH_PAGE_URL

# Define waste type icons
ICON_MAP = {
    "Next organic collection": "mdi:leaf",
    "Next rubbish collection": "mdi:trash-can",
    "Next recycling collection": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": f'Visit the [Glen Eira City Council]({SEARCH_PAGE_URL}) "Find your bin collection day" page and search for your address. There are typically no commas and the suburb / state name are in capitals. For example: 4 Staniland Grove ELSTERNWICK VIC 3185. The arguments should exactly match the full street address after selecting the autocomplete result.',
}

PARAM_DESCRIPTIONS = {
    "en": {
        _STREET_ADDRESS_ARG_NAME: "Full street address including suburb, state and postal code without separating commas.",
    },
    "de": {
        _STREET_ADDRESS_ARG_NAME: "Vollständige Straßenadresse einschließlich Stadtteil, Bundesland und Postleitzahl ohne Trennzeichen.",
    },
    "it": {
        _STREET_ADDRESS_ARG_NAME: "Indirizzo completo comprensivo di quartiere, regione e CAP, senza virgole di separazione.",
    },
    "fr": {
        _STREET_ADDRESS_ARG_NAME: "Adresse complète incluant le quartier, la région et le code postal, sans virgules de séparation.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        _STREET_ADDRESS_ARG_NAME: "Street Address",
    },
    "de": {
        _STREET_ADDRESS_ARG_NAME: "Straßenadresse",
    },
    "it": {
        _STREET_ADDRESS_ARG_NAME: "Indirizzo completo",
    },
    "fr": {
        _STREET_ADDRESS_ARG_NAME: "Adresse complète",
    },
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        if not self._street_address:
            raise SourceArgumentRequired(
                _STREET_ADDRESS_ARG_NAME, "A street address was not provided."
            )

        session = requests.Session()
        response = session.get(SEARCH_PAGE_URL)
        response.raise_for_status()

        # fetch autocomplete result
        _LOGGER.debug(
            "Searching the autocomplete API endpoint '%s' using term '%s'...",
            API_URL,
            self._street_address,
        )
        params: dict[str, str | int] = {
            "address": self._street_address,
        }

        response = session.get(
            API_URL,
            params=params,
        )
        response.raise_for_status()
        if "rubbish-and-street-cleaning" not in response.text:
            raise SourceArgumentNotFound(
                _STREET_ADDRESS_ARG_NAME,
                self._street_address,
                f"The provided address returned no results. Check your address on {SEARCH_PAGE_URL}",
            )
        soup = BeautifulSoup(response.text, "html.parser")

        div = soup.find("div", id="rubbish-and-street-cleaning")
        if div is None:
            raise SourceArgumentNotFound(
                _STREET_ADDRESS_ARG_NAME,
                self._street_address,
                f"The provided address returned no results. Check your address on {SEARCH_PAGE_URL}",
            )
        entries = []

        for child in div.find_all("div"):
            rubbish_type = child.find("h3").get_text()
            when = child.find("p").get_text()
            if rubbish_type in ICON_MAP:
                date = datetime.strptime(when, "%A %d %B %Y").date()
                entries.append(
                    Collection(date=date, t=rubbish_type, icon=ICON_MAP[rubbish_type])
                )

        return entries
