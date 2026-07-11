"""Stadtreinigung Gießen (stadtreinigung.giessen.de).

Demonstrates: a street lookup keyed by alphabet range rather than a search
endpoint -- the site's street dropdown is only ever rendered a page at a
time, filtered by a "von"/"bis" (from/to) letter-range query param, so
resolving one street name means loading its first letter's page and matching
within it. No configured retriever expresses "load one alphabet-range page,
fuzzy-match a street within it, then POST for the ICS download using the
same range", hence a source-defined ``retrieve()``.

The provider suffixes most labels with a cadence phrase (e.g. "Restmüll
wöchentlich", "Altpapier 4-wöchentlich"), so ``clean`` strips that down to
the bare category before it is mapped/resolved.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GARDEN_WASTE

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
    if select is not None:
        for option in select.find_all("option"):
            name = option.text.strip()
            value = option.get("value")
            if name and value is not None:
                streets[name] = value
    return streets


def _find_street_value(session, street_value: str) -> tuple[str, str, str]:
    """Find the street value by searching through the alphabet pages.

    Returns (street_value, von, bis): the street id and the alphabet-range
    params that page was loaded with (needed again for the ICS POST).
    """
    first_letter = street_value[0].upper()
    streets = _load_streets_for_letter(session, first_letter)
    von, bis = _alphabet_range(first_letter)

    if street_value in streets:
        return streets[street_value], von, bis

    street_lower = street_value.lower()
    for name, value in streets.items():
        if name.lower() == street_lower:
            return value, von, bis

    partial_matches = {
        name: value for name, value in streets.items() if street_lower in name.lower()
    }
    if len(partial_matches) == 1:
        return next(iter(partial_matches.values())), von, bis
    if len(partial_matches) > 1:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street_value, sorted(partial_matches)
        )
    raise SourceArgumentNotFoundWithSuggestions("street", street_value, sorted(streets))


@final
class Source(BaseSource):
    TITLE = "Stadtreinigung Gießen"
    DESCRIPTION = "Source for Stadtreinigung Gießen waste collection schedule."
    URL = "https://stadtreinigung.giessen.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

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

    parse = IcsParser()
    transform = ICSTransformer(
        clean=_clean_type,
        type_value_map={"Astwerkabfuhr": GARDEN_WASTE, "Weihnachtsbaum": GARDEN_WASTE},
    )

    def __init__(self, street: str, house_number: str):
        super().__init__(street=street.strip(), house_number=str(house_number).strip())

    def retrieve(self, source):
        session = source.session
        street_value = self.params["street"]
        house_number_value = self.params["house_number"]

        street_value_id, von, bis = _find_street_value(session, street_value)

        r = session.post(
            _BASE_URL,
            params={"von": von, "bis": bis},
            data={
                "strasse": street_value_id,
                "hausnr": house_number_value,
                "ical": " iCalendar",  # The button value
            },
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        return r
