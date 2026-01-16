import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

_STREET_ADDRESS_ARG_NAME = "street_address"
_LOGGER = logging.getLogger(__name__)

TITLE = "City of Casey"
DESCRIPTION = "Source for the City of Casey rubbish collection."
URL = "https://www.casey.vic.gov.au/"
TEST_CASES = {
    # "Empty Address": {_STREET_ADDRESS_ARG_NAME: ""},
    # "Invalid Address": {_STREET_ADDRESS_ARG_NAME: "Blah blah i dont exist"},
    # "Ambiguous Address": {_STREET_ADDRESS_ARG_NAME: "55 Vi"},
    "Butlers Kitchen": {
        _STREET_ADDRESS_ARG_NAME: "55 Victor Crescent NARRE WARREN VIC 3805"
    },
    "Daniel's Donuts Cranbourne": {
        _STREET_ADDRESS_ARG_NAME: "Shop 14/1085 South Gippsland Highway CRANBOURNE NORTH VIC 3977"
    },
}

SEARCH_PAGE_URL = "https://www.casey.vic.gov.au/find-your-bin-collection-day"
API_URL = "https://www.casey.vic.gov.au/coc-properties/api/search-address"

# Define waste type icons
ICON_MAP = {
    "Garden": "mdi:leaf",
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": f'Visit the [City of Casey]({SEARCH_PAGE_URL}) "Find your bin collection day" page and search for your address. There are typically no commas and the suburb / state name are in capitals. For example: 55 Victor Crescent NARRE WARREN VIC 3805. The arguments should exactly match the full street address after selecting the autocomplete result.',
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

# Collection date property name prefix / postfix
_PREV_STRING = "Prev"
_NEXT_STRING = "Next"
_DATE_STRING = "Date"


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        if not self._street_address:
            raise SourceArgumentRequired(
                _STREET_ADDRESS_ARG_NAME, "A street address was not provided."
            )

        session = requests.Session()

        # load the page you search from first to ensure the autocomplete works
        _LOGGER.debug(
            "Requesting search page URL '%s' to create a session to avoid captcha problems",
            SEARCH_PAGE_URL,
        )
        response = session.get(SEARCH_PAGE_URL)
        response.raise_for_status()

        # fetch autocomplete result
        _LOGGER.debug(
            "Searching the autocomplete API endpoint '%s' using term '%s'...",
            API_URL,
            self._street_address,
        )
        params: dict[str, str | int] = {
            "term": self._street_address,
            "status": "C,F",
            "land_area": 0,
            "types": "",
            "inclusion": 0,
            "prop_type_details": "",
            "separate_address": 0,
            "bin_collection_details": "true",
        }

        response = session.get(
            API_URL,
            params=params,
        )
        response.raise_for_status()
        search_results = response.json()
        if (
            "result" not in search_results
            or not isinstance(search_results["result"], list)
            or len(search_results["result"]) < 1
        ):
            raise SourceArgumentNotFound(
                _STREET_ADDRESS_ARG_NAME,
                self._street_address,
                f"The provided address returned no results. Check your address on {SEARCH_PAGE_URL}",
            )

        if len(search_results["result"]) > 1:
            address_suggestions = [x["full_address"] for x in search_results["result"]]
            raise SourceArgAmbiguousWithSuggestions(
                _STREET_ADDRESS_ARG_NAME, self._street_address, address_suggestions
            )

        entries = []

        for key, value in search_results["result"][0].items():
            # properties come through like "NextGarbageDate", "NextRecycleDate" or "PrevGardenDate" etc
            # extracting waste type name from the middle of "Next{x}Date" to support future waste types without direct mapping
            if key.endswith(_DATE_STRING) and (
                key.startswith(_NEXT_STRING) or key.startswith(_PREV_STRING)
            ):
                name = (
                    key.replace(_DATE_STRING, "")
                    .replace(_NEXT_STRING, "")
                    .replace(_PREV_STRING, "")
                )

                date = datetime.strptime(value, "%Y-%m-%d").date()
                icon = ICON_MAP[name] if name in ICON_MAP else None
                entries.append(Collection(date=date, t=name, icon=icon))

        return entries
