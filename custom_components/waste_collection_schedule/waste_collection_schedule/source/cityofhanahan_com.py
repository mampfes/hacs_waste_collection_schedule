import datetime
import re
from typing import Any, ClassVar, final

from bs4 import Tag
from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

# The City of Hanahan publishes its regular collection days as one page: a
# "<Weekday>:" paragraph followed by a list of "<Waste type> - <areas>" items.
# There is no address-to-route lookup, so the user picks one of the named
# service areas below, and each area is resolved against the live page by the
# text the city uses for it. Only the weekday is published; holiday and
# emergency changes are announced separately and are not reflected here.

_URL = (
    "https://www.cityofhanahan.com/publicworks/page/household-trash-collection-schedule"
)
_BODY = ".node-page__body-image-wrapper .field--name-body"

_HOUSEHOLD = "Household Waste"
_BROWN = "Brown Trash"
_YARD = "Yard Debris"
_METALS = "Metals"
_ELECTRONICS = "Electronic Scrap"

_CITYWIDE = "Citywide"
_PROPER = "Hanahan Proper"

# area -> (household waste anchor, yard debris anchor): the text the city's
# page uses for that area in each round. Brown trash, metals and electronic
# scrap are citywide. The Friday household-waste enclaves inside Hanahan Proper
# keep its Tuesday yard-debris day; the Tuesday household-waste streets are
# anchored on Loftis Rd, the first street the page names for that round.
_AREAS: dict[str, tuple[str, str]] = {
    _PROPER: (_PROPER, _PROPER),
    "Tanner Plantation": ("Tanner Plantation", "Tanner Plantation"),
    "Eagle Landing": ("Eagle Landing", "Eagle Landing"),
    "Otranto": ("Otranto", "Otranto"),
    "Spring Valley Mobile Home Park": ("Spring Valley mobile home park", _PROPER),
    "Gold Cup Springs": ("Gold cup springs", _PROPER),
    "North Rhett": ("North Rhett", _PROPER),
    "Lakeview subdivision": ("Lakeview subdivision", _PROPER),
    "Tuesday household waste area": ("Loftis Rd", _PROPER),
}

# The page separates the waste type from its areas with a hyphen or an en dash,
# not always surrounded by spaces ("Household Waste- Twin Oaks ...").
_ITEM_RE = re.compile(r"\s*[-–]\s*")
# "Hanahan Proper with the exception of ... (these homes are collected on
# Friday)": the enclaves named after "except" are not collected that day.
_EXCEPT_RE = re.compile(r"\bexcept", re.IGNORECASE)

_HORIZON_DAYS = 365


def _normalise(text: str) -> str:
    return " ".join(text.split()).casefold()


def _weekday_rounds(elements: list[Tag], source: Any) -> list[tuple[str, int]]:
    """Resolve the selected area to one ``(waste type, weekday)`` per round."""
    name = response_shape.source_name(source)
    rounds: dict[int, list[tuple[str, str]]] = {}
    day: int | None = None
    for element in elements:
        if element.name == "p":
            day = recurrence.weekday(element.get_text(" ", strip=True).rstrip(":"))
            continue
        if day is None:
            continue
        for item in element.find_all("li", recursive=False):
            parts = _ITEM_RE.split(item.get_text(" ", strip=True), maxsplit=1)
            if len(parts) != 2:
                continue
            kind, areas = parts
            rounds.setdefault(day, []).append(
                (kind.strip(), _normalise(_EXCEPT_RE.split(areas)[0]))
            )
        day = None

    response_shape.expect(
        set(rounds) == set(range(5)),
        source_name=name,
        detail=f"expected Monday-Friday lists, found weekdays {sorted(rounds)}",
    )

    household, yard = _AREAS[source.params["area"]]
    anchors = {
        _HOUSEHOLD: household,
        _BROWN: _CITYWIDE,
        _YARD: yard,
        _METALS: _CITYWIDE,
        _ELECTRONICS: _CITYWIDE,
    }
    resolved = []
    for kind, anchor in anchors.items():
        days = [
            weekday
            for weekday, items in sorted(rounds.items())
            if any(k == kind and _normalise(anchor) in listed for k, listed in items)
        ]
        response_shape.expect(
            len(days) == 1,
            source_name=name,
            detail=f"{kind} for {anchor!r} found on weekdays {days}",
        )
        resolved.append((kind, days[0]))
    return resolved


def _describe(record: tuple[str, int], source: Any):
    kind, weekday = record
    today = datetime.date.today()
    yield Schedule(
        kind,
        recurrence.next_weekday(weekday, on_or_after=today),
        recurrence.WEEKLY,
        until=today + datetime.timedelta(days=_HORIZON_DAYS),
    )


@final
class Source(BaseSource):
    TITLE = "Hanahan, SC"
    DESCRIPTION = "Regular curbside collection schedule for the City of Hanahan."
    URL = _URL
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@dmkjr"]

    TEST_CASES: ClassVar[dict] = {
        "Hanahan Proper": {"area": "Hanahan Proper"},
        "Tanner Plantation": {"area": "Tanner Plantation"},
        "Eagle Landing": {"area": "Eagle Landing"},
        "Otranto": {"area": "Otranto"},
        "Spring Valley Mobile Home Park": {"area": "Spring Valley Mobile Home Park"},
        "Tuesday household waste area": {"area": "Tuesday household waste area"},
    }

    PARAMS = (dropdown("area", list(_AREAS), label="Collection area"),)

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.GENERAL_WASTE,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
        wt.ELECTRONICS,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "The city publishes its collection days by named area, without an "
            'address lookup. Check the <a href="'
            f'{_URL}" target="_blank">household trash collection schedule</a> '
            "and select the area that serves your home. Spring Valley Mobile "
            "Home Park, Gold Cup Springs, North Rhett and Lakeview subdivision "
            "have their own household waste day; choose the Tuesday household "
            "waste area "
            "only for the streets and street segments the city lists under "
            "Tuesday. Holiday and emergency changes are not included."
        ),
    }

    retrieve = HttpGetRetriever(url=_URL)
    parse = HtmlParser(f"{_BODY} > p, {_BODY} > ul", require=[_BODY])
    preprocess = Compose(_weekday_rounds, RecurrenceExpander(_describe))
    transform = RowTransformer(
        type_value_map={
            _HOUSEHOLD: wt.GENERAL_WASTE,
            _BROWN: wt.BULKY_WASTE,
            _YARD: wt.GARDEN_WASTE,
            _METALS: wt.OTHER,
            _ELECTRONICS: wt.ELECTRONICS,
        },
        carry_raw_label=True,
    )
