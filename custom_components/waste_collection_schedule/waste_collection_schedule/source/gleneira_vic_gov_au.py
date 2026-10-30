"""City of Glen Eira (Victoria, Australia) kerbside collection days."""

from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.transformers import HtmlTransformer

SEARCH_PAGE_URL = "https://www.gleneira.vic.gov.au/our-city/in-your-area"

# The results page only answers for an address written exactly the way the
# council's register holds it ("4 Staniland Grove ELSTERNWICK VIC 3185"): no
# commas, spelled-out street type, upper-case suburb. The site's own address
# box does not send what was typed either; it sends the `value` of the
# autocomplete entry the visitor picked, so the address is resolved through the
# same endpoint before asking for the collections.
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
_STREET_WORDS = set(_STREET_TYPES.values())
# Trailing parts the register writes its own way ("VIC 3185"): they are left
# out of the search and of the comparison.
_STATES = {"VIC", "VICTORIA"}


def _words(value: str) -> list[str]:
    """Upper-case words, commas dropped, street types spelled out."""
    words = value.upper().replace(",", " ").split()
    return [_STREET_TYPES.get(word, word) for word in words]


def _significant(value: str) -> list[str]:
    """The words of an address without its state and postcode."""
    return [
        word
        for word in _words(value)
        if word not in _STATES and not (word.isdigit() and len(word) == 4)
    ]


def _query(street_address: str, **_) -> dict:
    """Search for the number and street only.

    The autocomplete matches a substring of its canonical address, so a suburb
    or postcode written differently would make it return nothing; the suburb
    is checked on the candidates instead.
    """
    words = _significant(street_address)
    for index, word in enumerate(words):
        if index and word in _STREET_WORDS:
            return {"text": " ".join(words[: index + 1])}
    return {"text": " ".join(words)}


def _address(response, *keys, street_address, **_) -> str:
    """The register's own wording of the configured address."""
    # The endpoint answers 404 for "nothing matched".
    candidates = response.json() if response.status_code != 404 else []
    if response.status_code not in (200, 404):
        response.raise_for_status()
    values = [str(c["value"]) for c in candidates or [] if c.get("value")]
    if not values:
        raise SourceArgumentNotFound(
            "street_address",
            street_address,
            f"the council does not know this address, check it on {SEARCH_PAGE_URL}",
        )
    wanted = _significant(street_address)
    exact = [v for v in values if _significant(v) == wanted]
    if len(exact) == 1:
        return exact[0]
    # The search is a substring match, so "4 Staniland Grove" also finds 14 and
    # 44, and the street in other suburbs. Keep the candidates with the same
    # number that contain every word that was typed.
    matching = [
        v
        for v in values
        if _significant(v)[:1] == wanted[:1] and set(wanted) <= set(_significant(v))
    ]
    if len(matching) == 1:
        return matching[0]
    raise SourceArgAmbiguousWithSuggestions(
        "street_address", street_address, matching or values
    )


@final
class Source(BaseSource):
    TITLE = "City of Glen Eira"
    DESCRIPTION = "Source for the Glen Eira City Council rubbish collection."
    URL = "https://www.gleneira.vic.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Elsternwick Library": {
            "street_address": "4 Staniland Grove ELSTERNWICK VIC 3185"
        },
        # The formats people actually type, none of which the results page
        # accepts verbatim: they are resolved through the council's own
        # autocomplete.
        "Comma separated": {
            "street_address": "4 Staniland Grove, Elsternwick VIC 3185"
        },
        "No suburb": {"street_address": "4 Staniland Grove"},
        "Abbreviated street type": {"street_address": "1 Nepean Hwy, Elsternwick"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"street_address": "999 Nowhere Boulevard"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            f'Visit the [Glen Eira City Council]({SEARCH_PAGE_URL}) "Find your bin '
            'collection day" page and search for your address, for example: 4 '
            "Staniland Grove ELSTERNWICK VIC 3185. The address is resolved through "
            "the council's own address lookup, so commas, lower case suburbs and "
            'abbreviated street types (e.g. "Hwy" for "Highway") are accepted as '
            "well. The council shows the next collection of each bin. Since the v3 "
            "pipeline migration, waste types use canonical, localised names. "
            "Update filters, automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = retrievers.Request(
        SEARCH_PAGE_URL,
        params=lambda address, **_: {"address": address},
        before=(
            retrievers.Lookup(
                AUTOCOMPLETE_URL,
                params=_query,
                pick=_address,
                raise_for_status=False,
            ),
        ),
    )

    # One box per service; street sweeping is a weekday rule, not a date.
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser(
            '#rubbish-and-street-cleaning .box:has(h3:-soup-contains("collection"))'
        ),
        argument="street_address",
        contains="rubbish-and-street-cleaning",
        hint=f"the council has no collection days for this address, see {SEARCH_PAGE_URL}",
    )

    transform = HtmlTransformer(
        date_getter=lambda element: element.find("p").get_text(strip=True),
        type_getter=lambda element: element.find("h3").get_text(strip=True),
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "Next rubbish collection": wt.GENERAL_WASTE,
            "Next recycling collection": wt.RECYCLABLES,
            "Next organic collection": wt.ORGANIC,
        },
    )
