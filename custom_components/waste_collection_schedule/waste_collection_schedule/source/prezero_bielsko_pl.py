import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import EvalJsonParser, eval_json
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://prezero-bielsko.pl/harmonogramy/index.php"
_CITY = "Bielsko-Biała"
_HEADERS = {
    "accept": "*/*",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
}


def _form(view: str, q: str, **fields: str) -> dict[str, str]:
    return {
        "option": "com_sita",
        "view": view,
        "q": q,
        **fields,
        "rok": str(datetime.date.today().year),
    }


def _street(response, *keys, street, **_) -> str:
    """The provider's spelling of the street, matched case-insensitively."""
    streets = [row["ulica"] for row in eval_json(response)["dane"] if "ulica" in row]
    for candidate in streets:
        if candidate.lower() == street.lower():
            return candidate
    raise SourceArgumentNotFoundWithSuggestions("street", street, streets)


def _house_number(response, *keys, house_number, **_) -> str:
    numbers = [row["numer"] for row in eval_json(response)["dane"] if "numer" in row]
    if house_number not in numbers:
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", house_number, numbers
        )
    return house_number


def _symbol(response, *keys, house_number, **_) -> str:
    """The id the schedule request is keyed by."""
    rows = eval_json(response)["dane"]
    if not rows:
        raise SourceArgumentNotFound("house_number", house_number)
    return rows[0]["symbol"]


def _date(record) -> datetime.date:
    return datetime.date(
        datetime.date.today().year, int(record["data_m"]), int(record["data_d"])
    )


@final
class Source(BaseSource):
    TITLE = "PreZero Bielsko-Biała"
    DESCRIPTION = "Source for PreZero Bielsko-Biała waste collection schedule"
    URL = "https://prezero-bielsko.pl/harmonogram-odbioru-odpadow/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"street": "Krakowska", "house_number": "12"},
        "Test_002": {"street": "1 Maja", "house_number": "10"},
        "Test_003": {"street": "Bajki", "house_number": "12A"},
        "Test_004": {"street": "Chabrowa", "house_number": "1B"},
    }

    PARAMS = (
        street("street"),
        house_number("house_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street and house number in Bielsko-Biała as they appear on "
            "https://prezero-bielsko.pl/harmonogram-odbioru-odpadow/."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                _API_URL,
                method="POST",
                headers=_HEADERS,
                data=lambda **_: _form("ulice", _CITY),
                pick=_street,
            ),
            Lookup(
                _API_URL,
                method="POST",
                headers=_HEADERS,
                data=lambda matched_street, **_: _form(
                    "numery", _CITY, ulica=matched_street
                ),
                pick=_house_number,
            ),
            Lookup(
                _API_URL,
                method="POST",
                headers=_HEADERS,
                data=lambda matched_street, number, **_: _form(
                    "typy", _CITY, ulica=matched_street, numer=number
                ),
                pick=_symbol,
            ),
        ),
        url=_API_URL,
        method="POST",
        headers=_HEADERS,
        data=lambda matched_street, number, symbol, **_: _form(
            "daty",  # codespell:ignore daty
            symbol,
        ),
    )
    parse = EvalJsonParser("dane")
    transform = JsonTransformer(
        date_key=_date,
        type_key="rodzaj",
        type_value_map={
            "kuchenne": wt.FOOD_WASTE,
            "resztkowe": wt.GENERAL_WASTE,
            "makulatura": wt.PAPER,
            "szklo": wt.GLASS,
            "mix": wt.RECYCLABLES,
            "zielone": wt.GARDEN_WASTE,
            "gabaryty": wt.BULKY_WASTE,
            # ash (popiół), a stream the legacy source reported as "unknown"
            "popiol": wt.OTHER,
        },
    )
