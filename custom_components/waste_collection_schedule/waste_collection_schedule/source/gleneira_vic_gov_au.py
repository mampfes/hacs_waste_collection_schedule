import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
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
    # The formats people actually type, none of which the results page accepts
    # verbatim -- they are resolved through the council's own autocomplete.
    "Comma separated": {
        _STREET_ADDRESS_ARG_NAME: "4 Staniland Grove, Elsternwick VIC 3185"
    },
    "No suburb": {_STREET_ADDRESS_ARG_NAME: "4 Staniland Grove"},
    "Abbreviated street type": {_STREET_ADDRESS_ARG_NAME: "1 Nepean Hwy, Elsternwick"},
}

SEARCH_PAGE_URL = "https://www.gleneira.vic.gov.au/our-city/in-your-area"
API_URL = SEARCH_PAGE_URL

# The results page only answers for an address written exactly the way the
# council's register holds it ("4 Staniland Grove ELSTERNWICK VIC 3185"): no
# commas, spelled-out street type, upper-case suburb. Anything else -- and a
# comma is the single most common thing a visitor types -- silently returns the
# no-results page. The site's own address box does not send what was typed
# either; it sends the `value` of the autocomplete entry the visitor picked, so
# resolve through the same endpoint before asking for the collections.
AUTOCOMPLETE_URL = "https://www.gleneira.vic.gov.au/api/nearby/addressautocomplete"

# Street-type abbreviations -> what the register spells out. The autocomplete
# matches on substrings, so "Nepean Hwy" finds nothing while "Nepean Highway"
# finds the street.
_STREET_TYPES = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BVD": "BOULEVARD",
    "BLVD": "BOULEVARD",
    "CCT": "CIRCUIT",
    "CL": "CLOSE",
    "CR": "CRESCENT",
    "CRES": "CRESCENT",
    "CT": "COURT",
    "DR": "DRIVE",
    "ESP": "ESPLANADE",
    "GDNS": "GARDENS",
    "GR": "GROVE",
    "GRV": "GROVE",
    "HWY": "HIGHWAY",
    "LN": "LANE",
    "PDE": "PARADE",
    "PL": "PLACE",
    "RD": "ROAD",
    "SQ": "SQUARE",
    "ST": "STREET",
    "TCE": "TERRACE",
    "WY": "WAY",
}

# Trailing tokens that carry no weight in the register's own substring search
# but do stop it matching, dropped one "layer" at a time when the full query
# comes back empty.
_STATES = {"VIC", "VICTORIA"}


def _normalise(value: str) -> str:
    """Upper-case, drop commas and collapse whitespace, for comparison."""
    return " ".join(value.upper().replace(",", " ").split())


def _expand_street_types(value: str) -> str:
    return " ".join(_STREET_TYPES.get(word, word) for word in value.split())


def _house_number(value: str) -> str | None:
    """The leading street number of an address, e.g. "4" or "12A"."""
    match = re.match(r"\s*(\d+[A-Za-z]?(?:[-/]\d+[A-Za-z]?)?)\b", value)
    return match.group(1).upper() if match else None


def _query_variants(address: str) -> list[str]:
    """Progressively shorter queries to try against the autocomplete.

    The endpoint matches on a substring of its canonical address, so a query
    carrying a postcode or state the register writes differently returns
    nothing at all. Shedding those trailing parts recovers the match without
    ever loosening what we then accept as the answer.
    """
    full = _expand_street_types(_normalise(address))
    variants = [full]
    words = full.split()
    while len(words) > 2:
        last = words[-1]
        if last.isdigit() and len(last) == 4:  # postcode
            words = words[:-1]
        elif last in _STATES:
            words = words[:-1]
        else:
            break
        variants.append(" ".join(words))
    # Last resort: number + street only, dropping the suburb.
    if len(words) > 3:
        variants.append(" ".join(words[:3]))
    return list(dict.fromkeys(v for v in variants if v))


# Define waste type icons
ICON_MAP = {
    "Next organic collection": Icons.ORGANIC,
    "Next rubbish collection": Icons.GENERAL_WASTE,
    "Next recycling collection": Icons.RECYCLING,
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

    def _autocomplete(self, session: requests.Session, text: str) -> list[dict]:
        """Candidates for a query, or [] when the council knows of none."""
        response = session.get(AUTOCOMPLETE_URL, params={"text": text}, timeout=30)
        # The endpoint answers 404 for "nothing matched", which is a normal
        # outcome here, not a transport failure.
        if response.status_code == 404:
            return []
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def _resolve_address(self, session: requests.Session) -> str:
        """Turn what the visitor typed into the register's own wording."""
        wanted = _expand_street_types(_normalise(self._street_address))
        wanted_number = _house_number(wanted)

        candidates: list[dict] = []
        for query in _query_variants(self._street_address):
            candidates = self._autocomplete(session, query)
            if candidates:
                break

        if not candidates:
            # Nothing to resolve against; let the results page have its own say
            # on the address as typed rather than refusing outright.
            return self._street_address

        values = [c["value"] for c in candidates if c.get("value")]

        exact = [v for v in values if _normalise(v) == wanted]
        if len(exact) == 1:
            return exact[0]

        # The autocomplete matches on a substring, so a query for "68 Glen Eira
        # Road" also returns "268 Glen Eira Road". Keep only the properties
        # whose street number is the one that was actually asked for.
        if wanted_number:
            same_number = [v for v in values if _house_number(v) == wanted_number]
            if len(same_number) == 1:
                return same_number[0]
            if same_number:
                values = same_number

        if len(values) == 1:
            return values[0]

        raise SourceArgAmbiguousWithSuggestions(
            _STREET_ADDRESS_ARG_NAME, self._street_address, values
        )

    def fetch(self) -> list[Collection]:
        if not self._street_address:
            raise SourceArgumentRequired(
                _STREET_ADDRESS_ARG_NAME, "A street address was not provided."
            )

        session = requests.Session()
        response = session.get(SEARCH_PAGE_URL)
        response.raise_for_status()

        address = self._resolve_address(session)

        _LOGGER.debug(
            "Requesting collections from '%s' for resolved address '%s'...",
            API_URL,
            address,
        )
        params: dict[str, str | int] = {
            "address": address,
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
