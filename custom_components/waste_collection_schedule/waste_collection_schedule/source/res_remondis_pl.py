"""REMONDIS harmonogram (res.remondis.pl), e.g. Sosnowiec.

Composes: :class:`~waste_collection_schedule.retrievers.YearlyRetriever`. The
address resolves through three cascading lookups (city, street, house number);
the house number's reply carries the property id and a short-lived token. Each
year then costs three requests: the id of the year, a report request that
returns the path of a generated HTML schedule, and the download of that file.
The schedule is a table with a row per month and a column per waste type, each
cell listing the collection days of that month.
"""

import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_API = "https://res.remondis.pl/harmonogram"

_MONTHS = {
    "STYCZEN": 1,
    "LUTY": 2,
    "MARZEC": 3,
    "KWIECIEN": 4,
    "MAJ": 5,
    "CZERWIEC": 6,
    "LIPIEC": 7,
    "SIERPIEN": 8,
    "WRZESIEN": 9,
    "PAZDZIERNIK": 10,
    "LISTOPAD": 11,
    "GRUDZIEN": 12,
}
_ACCENTS = str.maketrans("ĄĆĘŁŃÓŚŹŻąćęłńóśźż", "ACELNOSZZacelnoszz")
_YEAR_RE = re.compile(r"w poszczególnych miesiącach (\d{4})")

_TYPE_MAP = {
    "ODPADY ZMIESZANE pozostałe po segregacji": wt.GENERAL_WASTE,
    "PAPIER": wt.PAPER,
    "METALE I TWORZYWA SZTUCZNE": wt.RECYCLABLES,
    "SZKŁO": wt.GLASS,
    "ODPADY BIO": wt.ORGANIC,
    "ODPADY ZIELONE": wt.GARDEN_WASTE,
    "ODPADY WIELKOGABARYTOWE": wt.BULKY_WASTE,
    "POPIÓŁ": wt.OTHER,
}


def _norm(value: str) -> str:
    return " ".join(str(value).translate(_ACCENTS).upper().split())


def _pick_named(argument: str):
    """Pick the entry of a ``[{id, value}]`` list whose value equals the argument."""

    def pick(response, *_keys, **params):
        wanted = params[argument]
        entries = response.json()
        for entry in entries:
            if _norm(entry["value"]) == _norm(wanted):
                return entry["id"]
        raise SourceArgumentNotFoundWithSuggestions(
            argument, wanted, [entry["value"] for entry in entries]
        )

    return pick


def _pick_number(response, *_keys, house_number, **_):
    entries = response.json()
    for entry in entries:
        if _norm(entry["value"]) == _norm(house_number):
            return entry["id"], entry["token"]
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", house_number, [entry["value"] for entry in entries]
    )


def _pick_year(response, year, *_keys, **_):
    for entry in response.json():
        if str(entry["value"]) == str(year):
            return entry["id"]
    raise SourceArgumentNotFound("year", year)


def _month_rows(tables, source=None):
    """``(date, label)`` rows of the schedule table; one table per response."""
    for table in tables:
        year_match = _YEAR_RE.search(table.get_text(" "))
        header = table.find("thead")
        if year_match is None or header is None:
            raise ValueError("REMONDIS schedule layout changed")
        year = int(year_match.group(1))
        labels = [th.get_text(strip=True) for th in header.find_all("tr")[-1]("th")]
        for row in table.find("tbody").find_all("tr"):
            cells = [td.get_text(strip=True) for td in row("td")]
            month = _MONTHS.get(_norm(cells[0]))
            if month is None:
                raise ValueError(f"unknown month {cells[0]!r}")
            for label, cell in zip(labels[1:], cells[1:], strict=True):
                if label not in _TYPE_MAP:
                    continue
                for day in re.findall(r"\d+", cell):
                    yield datetime.date(year, month, int(day)), label


@final
class Source(BaseSource):
    TITLE = "REMONDIS (res.remondis.pl)"
    DESCRIPTION = "Source for REMONDIS waste collection schedules (e.g. Sosnowiec)."
    URL = "https://res.remondis.pl/harmonogram/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Sosnowiec, Malinowa 6": {
            "city": "Sosnowiec",
            "street": "Malinowa",
            "house_number": "6",
        },
    }

    PARAMS = (city(), street(), house_number())

    retrieve = retrievers.YearlyRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(f"{_API}/addresses/cities", pick=_pick_named("city")),
            retrievers.Lookup(
                lambda city_id, **_: f"{_API}/addresses/streets/{city_id}",
                pick=_pick_named("street"),
            ),
            retrievers.Lookup(
                lambda city_id, street_id, **_: (
                    f"{_API}/addresses/numbers/{city_id}/{street_id}"
                ),
                pick=_pick_number,
            ),
        ),
        fetch=retrievers.Request(
            lambda year, context, year_id, file_path, **_: file_path,
            encoding="utf-8",
            before=(
                retrievers.Lookup(f"{_API}/years", pick=_pick_year),
                retrievers.Lookup(
                    f"{_API}/reports",
                    params=lambda year, context, year_id, **_: {
                        "type": "html",
                        "id": context[2][0],
                        "responseType": "json",
                        "token": context[2][1],
                        "yearId": year_id,
                    },
                    pick=lambda response, *_keys, **_: response.json()["filePath"],
                ),
            ),
        ),
    )
    parse = parsers.EachResponse(
        parsers.HtmlParser(".tableTemplate table", require=["thead", "tbody"]),
        then=_month_rows,
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
