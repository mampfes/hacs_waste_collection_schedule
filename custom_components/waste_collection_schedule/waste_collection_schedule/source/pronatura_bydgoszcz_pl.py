from collections.abc import Iterator
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://zs5cv4ng75.execute-api.eu-central-1.amazonaws.com/prod"

_MONTHS = {
    "Styczeń": 1,
    "Luty": 2,
    "Marzec": 3,
    "Kwiecień": 4,
    "Maj": 5,
    "Czerwiec": 6,
    "Lipiec": 7,
    "Sierpień": 8,
    "Wrzesień": 9,
    "Październik": 10,
    "Listopad": 11,
    "Grudzień": 12,
}


def _street_id(response, *keys, street_name, **_) -> str:
    streets = response.json()
    wanted = str(street_name).upper()
    for row in streets:
        if row["street"].upper() == wanted:
            return row["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_name", wanted, [row["street"] for row in streets]
    )


def _address_id(response, *keys, street_number, **_) -> str:
    addresses = response.json()
    wanted = str(street_number).upper()
    for row in addresses:
        if row["buildingNumber"].upper() == wanted:
            return row["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_number", wanted, [row["buildingNumber"] for row in addresses]
    )


def _days(schedule: Any, source: Any = None) -> Iterator[dict[str, str]]:
    """One record per collection day, from the per-month, per-type day lists."""
    year = schedule["year"]
    for month in schedule["trashSchedule"]:
        number = _MONTHS[month["month"]]
        for entry in month["schedule"]:
            for day in entry["days"]:
                yield {
                    "date": f"{year}-{number:02d}-{int(day):02d}",
                    "type": entry["type"],
                }


@final
class Source(BaseSource):
    TITLE = "Bydgoszcz Pronatura"
    DESCRIPTION = "Source for Bydgoszcz city garbage collection by Pronatura"
    URL = "http://www.pronatura.bydgoszcz.pl/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Case1": {
            "street_name": "LEGNICKA",
            "street_number": 1,
        },
        "Case2": {
            "street_name": "JÓZEFA SOWIŃSKIEGO",
            "street_number": "22A",
        },
    }

    PARAMS = (
        street("street_name"),
        house_number("street_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name and building number in Bydgoszcz as they "
            "appear in the Pronatura schedule. Neither is case-sensitive."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(f"{_API}/streets", pick=_street_id),
            retrievers.Lookup(
                lambda sid, **_: f"{_API}/address-points/{sid}", pick=_address_id
            ),
        ),
        url=lambda sid, aid, **_: f"{_API}/trash-schedule/{aid}",
    )

    parse = parsers.JsonParser()

    preprocess = staticmethod(_days)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "odpady zmieszane": wt.GENERAL_WASTE,
            "papier": wt.PAPER,
            "plastik": wt.RECYCLABLES,
            "szkło": wt.GLASS,
            "odpady bio": wt.ORGANIC,
            "odpady wielkogabarytowe": wt.BULKY_WASTE,
        },
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )
