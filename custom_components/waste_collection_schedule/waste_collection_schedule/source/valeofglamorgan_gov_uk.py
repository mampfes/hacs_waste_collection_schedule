import datetime
import re
from typing import ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://myvale.valeofglamorgan.gov.uk/getdata.aspx"

# Recycling and food are collected every week on the weekday the API names; the
# council publishes no dates for them, so ten weeks are projected.
_WEEKS = 10


def _api_params(uprn, **_) -> dict:
    return {
        "RequestType": "LocalInfo",
        "ms": "ValeOfGlamorgan/AllMaps",
        "group": "Waste|new_refuse",
        "uid": uprn,
    }


def _api_record(response, source=None) -> list:
    """The one record of waste details the API holds for the property."""
    return [response.json()["Results"]["waste"]]


def _calendar_urls(response, **params) -> dict:
    """The waste details for the property; an unknown UPRN is answered with text."""
    try:
        return _api_record(response)[0]
    except (ValueError, KeyError, TypeError):
        raise SourceArgumentNotFound(
            "uprn", params["uprn"], "no property found for this UPRN."
        ) from None


def _targets(source, waste) -> list[str]:
    """The API response again (for the weekday) and each published calendar."""
    urls = [f"{_API_URL}?{urlencode(_api_params(**source.params))}"]
    for key in ("residual_calendar_url", "green_calendar_url"):
        if waste.get(key):
            urls.append(waste[key])
    return urls


def _rows(records, source):
    """``(date, label)`` rows from the weekday record and the calendar tables.

    The API record names the weekday of the weekly recycling and food round. Each
    calendar page is a table whose header row names the bin and whose body rows
    give a month and the days in it ("2 and 23"; "Book and request" for months
    without a service).
    """
    label = None
    for record in records:
        if isinstance(record, dict):
            name = record["recycling_food"]
            weekday = recurrence.weekday(name)
            if weekday is None:
                raise ValueError(f"Unknown recycling_food: {name}")
            first = recurrence.next_weekday(weekday)
            for date in recurrence.recurring(first, recurrence.WEEKLY, _WEEKS):
                yield date, "Recycling"
                yield date, "Food"
            continue
        if record.select_one("th"):
            label = record.select("th")[-1].get_text(strip=True)
            continue
        cells = record.select("td")
        if label is None or len(cells) != 2:
            continue
        parts = cells[0].get_text(strip=True).split()
        month = recurrence.month(parts[0]) if len(parts) == 2 else None
        if month is None or not parts[1].isdigit():
            continue
        for day in re.split(r"\s*(?:,|and)\s*", cells[1].get_text(strip=True)):
            if day.isdigit():
                yield datetime.date(int(parts[1]), month, int(day)), label


@final
class Source(BaseSource):
    TITLE = "Vale of Glamorgan Council"
    DESCRIPTION = "Source for Vale of Glamorgan Council."
    URL = "https://valeofglamorgan.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "CF62 7JP": {"uprn": 64003486},
        "CF32 0PW": {"uprn": 64017161},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
    ]

    PARAMS = (uprn("uprn"),)

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_API_URL, params=_api_params, pick=_calendar_urls),
        targets=_targets,
        fetch=retrievers.Request(lambda target, waste, **_: target),
    )
    parse = parsers.EachResponse(
        parsers.ByBodyPrefix(
            {"{": _api_record},
            default=parsers.HtmlParser("table tr"),
        )
    )
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Black bag collection date": wt.GENERAL_WASTE,
            "Garden waste collection date": wt.GARDEN_WASTE,
        }
    )
