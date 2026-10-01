import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://buergerportal.awl-neuss.de/api/v1/calendar"


def _street_code(response, **params):
    """The street number of the configured street name."""
    streets = response.json()
    name = params["street_name"]
    for item in streets:
        if item["strasseBezeichnung"] == name:
            return item["strasseNummer"]
    raise SourceArgumentNotFoundWithSuggestions(
        "street_name", name, [item["strasseBezeichnung"] for item in streets]
    )


def _given_street_code(**params):
    return params.get("street_code")


def _rows(data, source=None) -> list[tuple[datetime.date, str]]:
    """Flatten ``{"<month 0-11>-<year>": {"<day>": [colour, ...]}}`` into rows."""
    rows = []
    for key, days in data.items():
        month, year = (int(part) for part in key.split("-"))
        for day, colours in days.items():
            date = datetime.date(year, month + 1, int(day))
            rows.extend((date, colour) for colour in colours)
    return rows


@final
class Source(BaseSource):
    TITLE = "AWL Neuss"
    DESCRIPTION = "Source for Bürgerportal AWL Neuss waste collection."
    URL = "https://buergerportal.awl-neuss.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Neuss, Theodor-Heuss-Platz 13": {"street_code": 8650, "building_number": 13},
        "Neuss, Niederstrasse 42": {"street_code": 6810, "building_number": 42},
        "Neuss, Bahnhofstrasse 67": {
            "street_name": "Bahnhofstrasse",
            "building_number": 67,
        },
        "Neuss, Bismarckstrasse 52": {
            "street_name": "Bismarckstrasse",
            "building_number": 52,
        },
        "Neuss, Karlsstrasse 1 (5200)": {"street_code": "5200", "building_number": 1},
    }

    PARAMS = (
        alternatives(
            [street("street_name")],
            [text_field("street_code", "Street code")],
        ),
        house_number("building_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter either the exact street name (street_name) or the street code "
            "(street_code), together with the house number (building_number)."
        ),
        "de": (
            "Geben Sie entweder den genauen Straßennamen (street_name) oder den "
            "Straßencode (street_code) zusammen mit der Hausnummer "
            "(building_number) an."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API_URL}/townarea-streets",
                given=_given_street_code,
                pick=_street_code,
            ),
        ),
        url=API_URL,
        params=lambda resolved_code, *, building_number, **_: {
            "streetNum": resolved_code,
            "homeNummber": building_number,
            "startMonth": datetime.datetime.now().year,
            "isTreeMonthRange": "false",
            "isYear": "true",
        },
    )
    parse = parsers.JsonParser()
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        type_value_map={
            "grau": wt.GENERAL_WASTE,
            "pink": wt.GENERAL_WASTE,
            "braun": wt.ORGANIC,
            "blau": wt.PAPER,
            "gelb": wt.RECYCLABLES,
        },
        carry_raw_label=True,
    )
