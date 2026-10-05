from collections.abc import Iterator
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://api.ecoszczecin.pl/api/v1"
_LOCATION = "SZCZECIN"


def _street(response, *keys, street, **_) -> str:
    """The provider's spelling of the street, matched case-insensitively."""
    streets = response.json().get("data", [])
    wanted = street.strip().casefold()
    for candidate in streets:
        if candidate.casefold() == wanted:
            return candidate
    raise SourceArgumentNotFoundWithSuggestions("street", street, suggestions=streets)


def _number(response, *keys, house_number, **_) -> str:
    numbers = response.json().get("data", [])
    wanted = house_number.strip().casefold()
    for candidate in numbers:
        if candidate.casefold() == wanted:
            return candidate
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", house_number, suggestions=numbers
    )


def _days(calendar: Any, source: Any = None) -> Iterator[dict[str, str]]:
    """``{year: {month: [{"date": ..., "types": [...]}]}}`` as one record per type."""
    if not isinstance(calendar, dict):
        return
    for months in calendar.values():
        for days in months.values():
            for day in days:
                for waste_type in day.get("types", []):
                    yield {"date": day["date"], "type": waste_type}


@final
class Source(BaseSource):
    TITLE = "EcoSzczecin"
    DESCRIPTION = "Source for waste collection schedules in Szczecin, Poland, provided by ecoszczecin.pl."
    URL = "https://ecoszczecin.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Tczewska 7A": {"street": "TCZEWSKA", "house_number": "7A"},
        "Aleja Piastów 1": {"street": "ALEJA PIASTÓW", "house_number": "1"},
        "Bolesława Krzywoustego 1": {
            "street": "Bolesława Krzywoustego",
            "house_number": "1",
        },
    }

    PARAMS = (
        street("street"),
        house_number("house_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://ecoszczecin.pl/harmonogramy/, choose your street and "
            "house number from the dropdowns, and enter their values as shown. "
            "The street is not case-sensitive."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(f"{_API}/search/locations", pick=_street),
            retrievers.Lookup(
                f"{_API}/search/number",
                params=lambda matched_street, **_: {
                    "filter[location]": _LOCATION,
                    "filter[street]": matched_street,
                },
                pick=_number,
            ),
        ),
        url=f"{_API}/search/calendar",
        params=lambda matched_street, number, **_: {
            "filter[location]": _LOCATION,
            "filter[street]": matched_street,
            "filter[number]": number,
        },
    )

    parse = parsers.JsonParser("calendar")

    preprocess = staticmethod(_days)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Odpady zmieszane": wt.GENERAL_WASTE,
            "Bioodpady": wt.ORGANIC,
            "Metale i tworzywa sztuczne": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Szkło": wt.GLASS,
            "Odpady wielkogabarytowe": wt.BULKY_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
