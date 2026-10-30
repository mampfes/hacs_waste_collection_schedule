"""Fairfield City Council (NSW, Australia) kerbside collection days."""

import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://kerbside.fairfieldcity.nsw.gov.au/kerbside/"
# The council's own autocomplete list. The form only answers for a value taken
# verbatim from it, and the list was switched from abbreviated street types
# ("Dawson ST") to spelled-out ones ("Dawson Street"), which silently broke
# every previously valid saved value.
AUTOCOMPLETE_URL = f"{API_URL}fcc-autocomplete.js"
_STREET_LIST = re.compile(r"arrAddressStreetAndSuburb\s*=\s*\[(.*?)\]", re.DOTALL)

# Street-type abbreviations seen in the old list and in what people type.
_STREET_TYPES = {
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BVD": "BOULEVARD",
    "CCT": "CIRCUIT",
    "CH": "CHASE",
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
    "LP": "LOOP",
    "PDE": "PARADE",
    "PKWY": "PARKWAY",
    "PL": "PLACE",
    "RD": "ROAD",
    "RSE": "RISE",
    "SQ": "SQUARE",
    "ST": "STREET",
    "TCE": "TERRACE",
    "WY": "WAY",
}


def _canonical(value: str) -> str:
    """Upper-case words only, single-spaced, street types spelled out.

    Comparing on this lets a stored "Dawson ST, FAIRFIELD HEIGHTS" match the
    list's current "Dawson Street, FAIRFIELD HEIGHTS", and vice versa.
    """
    words = re.findall(r"\w+", value.upper())
    return " ".join(_STREET_TYPES.get(w, w) for w in words)


def _street_and_suburb(response, *keys, street_and_suburb, **_) -> str:
    """The list's own spelling of the configured street and suburb.

    The list is a convenience, not the lookup itself: when it cannot be read
    (an error status, a restructured script) the value is sent as typed.
    """
    typed = str(street_and_suburb).strip()
    match = _STREET_LIST.search(response.text) if response.ok else None
    streets = re.findall(r'"([^"]+)"', match.group(1)) if match else []
    if not streets:
        return typed
    wanted = _canonical(typed)
    for candidate in streets:
        if _canonical(candidate) == wanted:
            return candidate
    raise SourceArgumentNotFoundWithSuggestions("street_and_suburb", typed, streets)


@final
class Source(BaseSource):
    TITLE = "Fairfield City Council"
    DESCRIPTION = "Source for Fairfield City Council bin collection, NSW, Australia."
    URL = "https://kerbside.fairfieldcity.nsw.gov.au/kerbside/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "1 Dawson Street, FAIRFIELD HEIGHTS": {
            "street_number": "1",
            "street_and_suburb": "Dawson Street, FAIRFIELD HEIGHTS",
        },
        "12 Zadro Avenue, BOSSLEY PARK": {
            "street_number": "12",
            "street_and_suburb": "Zadro Avenue, BOSSLEY PARK",
        },
        # Abbreviated street types: what the council's autocomplete used to
        # emit, and therefore what most existing configurations still contain.
        "1 Dawson ST, FAIRFIELD HEIGHTS (abbreviated)": {
            "street_number": "1",
            "street_and_suburb": "Dawson ST, FAIRFIELD HEIGHTS",
        },
        "12 Zadro AVE, BOSSLEY PARK (abbreviated)": {
            "street_number": "12",
            "street_and_suburb": "Zadro AVE, BOSSLEY PARK",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {
            "street_number": "1",
            "street_and_suburb": "Nowhere Street, FAIRFIELD",
        },
    }

    PARAMS = (
        house_number("street_number"),
        street("street_and_suburb"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://kerbside.fairfieldcity.nsw.gov.au/kerbside/ and start "
            "typing your street name and suburb into the 'Street name & Suburb' "
            "field. Use the autocomplete suggestion (e.g. 'Dawson Street, "
            "FAIRFIELD HEIGHTS') as the street, including the suburb, and enter "
            "just your street number (e.g. 1, 7A, 7/10) as the house number. "
            "Abbreviated street types from older configurations (e.g. 'Dawson ST, "
            "FAIRFIELD HEIGHTS') are still accepted. The council shows the next "
            "collection of each bin. Since the v3 pipeline migration, waste types "
            "use canonical, localised names. Update filters, automations and "
            "customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = retrievers.Request(
        API_URL,
        method="POST",
        before=(
            retrievers.Lookup(
                AUTOCOMPLETE_URL, pick=_street_and_suburb, raise_for_status=False
            ),
        ),
        data=lambda resolved, street_number, **_: {
            "myStreetNumber": str(street_number).strip(),
            "myStreetAndSuburb": resolved,
        },
    )

    # One paragraph per bin: its picture names the bin, the bold text is the
    # date of its next collection.
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("#fcc-results-area p:has(> img[alt]):has(> strong)"),
        argument="street_and_suburb",
        contains='id="fcc-results-area"',
        hint=(
            "The council has no collection days for this address. Check it on "
            "https://kerbside.fairfieldcity.nsw.gov.au/kerbside/."
        ),
    )

    transform = HtmlTransformer(
        date_getter=lambda element: element.find("strong").get_text(strip=True),
        type_getter=lambda element: element.find("img")["alt"],
        parse_date=date_parsers.for_format("%A, %d/%m/%Y"),
        type_value_map={
            "Red bin": wt.GENERAL_WASTE,
            "Yellow bin": wt.RECYCLABLES,
            "Green bin": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
