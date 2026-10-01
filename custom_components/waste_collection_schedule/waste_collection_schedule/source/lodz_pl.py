import json
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, integer, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

_NO_SCHEDULE = "Brak dostępnego harmonogramu dla wskazanego adresu"
_EVENTS = re.compile(r"events:\s*(\[.*?\])\s*,\s*eventDidMount", re.DOTALL)


def _events(page: str, source: Any = None) -> list[dict]:
    """The FullCalendar ``events: [...]`` array embedded in the page's script."""
    params = getattr(source, "params", None) or {}
    address = (
        f"{params.get('street')} {params.get('house_number')} "
        f"({params.get('building_type')})"
    )
    if _NO_SCHEDULE in page:
        raise SourceArgumentNotFound("street/house_number/building_type", address)
    match = _EVENTS.search(page)
    if not match:
        raise SourceArgumentNotFound(
            "street/house_number/building_type",
            address,
            "Page retrieved, but calendar data (JSON) was not found.",
        )
    return [e for e in json.loads(match.group(1)) if e.get("title") and e.get("start")]


@final
class Source(BaseSource):
    TITLE = "Łódź"
    DESCRIPTION = "Source for Łódź city garbage collection"
    URL = "https://kartalodzianina.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Podchorążych 1 (Letniskowa)": {
            "street": "Podchorążych",
            "house_number": "1",
            "building_type": 3,
        },
        "Piotrkowska 104 (Wielorodzinna)": {
            "street": "Piotrkowska",
            "house_number": "104",
            "building_type": 2,
        },
        "Partyzantów 1 (Jednorodzinna)": {
            "street": "Partyzantów",
            "house_number": "1",
            "building_type": 1,
        },
    }

    PARAMS = (
        street("street"),
        house_number("house_number"),
        integer("building_type", "Building type", default=1),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name and house number as on kartalodzianina.pl "
            "(e.g. 'Piotrkowska' and '104'). building_type is 1 for a "
            "single-family house (default), 2 for a multi-family building or 3 "
            "for a summer house."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://kartalodzianina.pl/wywoz-odpadow",
        params=lambda street, house_number, building_type, **_: {
            "iframe": "",
            "actionPerformedWyszukajTyp": "",
            "odpad": "",
            "ulica": street,
            "nrDomu": str(house_number),
            "idMiejscowosci": "undefined",
            "rodzajZabudowy": building_type,
        },
        timeout=30,
    )

    parse = parsers.TextParser()

    preprocess = staticmethod(_events)

    transform = JsonTransformer(
        date_key="start",
        type_key="title",
        type_value_map={
            "Szkło": wt.GLASS,
            "Papier": wt.PAPER,
            "Metale i tworzywa sztuczne": wt.RECYCLABLES,
            "Resztkowe": wt.GENERAL_WASTE,
            "Mokre Bio": wt.ORGANIC,
            "Gabaryty": wt.BULKY_WASTE,
            "Odpady zielone": wt.GARDEN_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
