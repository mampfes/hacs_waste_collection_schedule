"""Stadtreinigung Gießen (stadtreinigung.giessen.de).

A street lookup keyed by alphabet range rather than a search endpoint: the
site's street dropdown is only ever rendered a page at a time, filtered by a
"von"/"bis" (from/to) letter-range query param, so resolving one street name
means loading its first letter's page and matching within it. That is the
lookup step below; the shared ``LookupChainRetriever`` then POSTs for the ICS
download using the same range.

The provider suffixes most labels with a cadence phrase (e.g. "Restmüll
wöchentlich", "Altpapier 4-wöchentlich"), so ``clean`` strips that down to
the bare category before it is mapped/resolved.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://stadtreinigung.giessen.de/akal/akal1.php"


def _clean_type(label: str) -> str:
    """Strip the provider's cadence suffix (e.g. " 4-wöchentlich") off a label."""
    lower = label.lower()
    if "restmüll" in lower:
        return "Restmüll"
    if "altpapier" in lower:
        return "Altpapier"
    return label


def _alphabet_range(letter: str) -> tuple[str, str]:
    """The 'von'/'bis' params selecting the dropdown page for one letter."""
    letter = letter.upper()
    if letter == "Z":
        # For Z, use [ which comes after Z in ASCII.
        return letter, "["
    return letter, chr(ord(letter) + 1)


def _load_streets_for_letter(session, letter: str) -> dict[str, str]:
    """Load all streets starting with the given letter."""
    von, bis = _alphabet_range(letter)
    r = session.get(_BASE_URL, params={"von": von, "bis": bis})
    r.raise_for_status()
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    select = soup.find("select", {"name": "strasse"})
    streets: dict[str, str] = {}
    if isinstance(select, Tag):
        for option in select.find_all("option"):
            name = option.text.strip()
            value = option.get("value")
            if name and value is not None:
                streets[name] = str(value)
    return streets


def _find_street_value(source: BaseSource, keys: tuple) -> str:
    """Find the street's id by searching through its alphabet page.

    The alphabet range that page was loaded with is needed again for the ICS
    POST, but it follows from the street's first letter, so the request
    callables recompute it rather than carrying it along.
    """
    street_value = source.params["street"]
    first_letter = street_value[0].upper()
    streets = _load_streets_for_letter(source.session, first_letter)

    if street_value in streets:
        return streets[street_value]

    street_lower = street_value.lower()
    for name, value in streets.items():
        if name.lower() == street_lower:
            return value

    partial_matches = {
        name: value for name, value in streets.items() if street_lower in name.lower()
    }
    if len(partial_matches) == 1:
        return next(iter(partial_matches.values()))
    if len(partial_matches) > 1:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street_value, sorted(partial_matches)
        )
    raise SourceArgumentNotFoundWithSuggestions("street", street_value, sorted(streets))


def _range_params(street: str) -> dict[str, str]:
    """The 'von'/'bis' query params for the street's alphabet page."""
    von, bis = _alphabet_range(street[0])
    return {"von": von, "bis": bis}


@final
class Source(BaseSource):
    TITLE = "Stadtreinigung Gießen"
    DESCRIPTION = "Source for Stadtreinigung Gießen waste collection schedule."
    URL = "https://stadtreinigung.giessen.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        GARDEN_WASTE,
        GENERAL_WASTE,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Achstattring 1": {
            "street": "Achstattring",
            "house_number": "1",
        },
        "Berliner Platz 5": {
            "street": "Berliner Platz",
            "house_number": "5",
        },
        "Marktplatz 10": {
            "street": "Marktplatz",
            "house_number": "10",
        },
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
    )

    retrieve = LookupChainRetriever(
        steps=(_find_street_value,),
        url=_BASE_URL,
        method="POST",
        params=lambda street_id, street, **_: _range_params(street),
        data=lambda street_id, street, house_number, **_: {
            "strasse": street_id,
            "hausnr": house_number,
            "ical": " iCalendar",  # The button value
        },
        raise_for_status=True,
        encoding="utf-8",
    )
    parse = IcsParser()
    transform = ICSTransformer(
        clean=_clean_type,
        type_value_map={"Astwerkabfuhr": GARDEN_WASTE, "Weihnachtsbaum": GARDEN_WASTE},
    )

    def __init__(self, street: str, house_number: str):
        super().__init__(street=street.strip(), house_number=str(house_number).strip())
