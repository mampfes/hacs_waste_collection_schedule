import datetime
import re
from typing import Any, ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, recurrence, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.preprocessors import Compose
from waste_collection_schedule.transformers import RowTransformer

_DATE_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{2}")
_PARSE_HOLIDAY = date_parsers.for_format("%m/%d/%y")
_WASTE = "Waste"
_WEEKS = 52


def _schedule(
    tags: list[Tag], source: "BaseSource | None" = None
) -> list[tuple[datetime.date, str]]:
    """Weekly collection on the published weekday, pushed one day later when a
    holiday falls earlier in the same Monday-Sunday week."""
    day_tag = next(
        (t for t in tags if "serviceguidelines_highight" in t.get("class", [])), None
    )
    weekday = recurrence.weekday(day_tag.get_text(strip=True)) if day_tag else None
    response_shape.expect(
        weekday is not None,
        source_name=response_shape.source_name(source),
        detail="collection weekday not found",
    )

    holidays: list[datetime.date] = []
    for tag in tags:
        if "holiday_cell" not in tag.get("class", []):
            continue
        match = _DATE_RE.search(tag.get_text())
        if match:
            try:
                holidays.append(_PARSE_HOLIDAY(match.group()))
            except ValueError:
                continue

    assert weekday is not None
    rows = []
    for day in recurrence.recurring(
        recurrence.next_weekday(weekday), recurrence.WEEKLY, _WEEKS
    ):
        week_start = day - datetime.timedelta(days=day.weekday())
        if any(week_start <= holiday < day for holiday in holidays):
            day += datetime.timedelta(days=1)
        rows.append((day, _WASTE))
    return rows


@final
class Source(BaseSource):
    TITLE = "Village of Sunbury, Ohio"
    DESCRIPTION = "Source for Village of Sunbury, Ohio"
    URL = "https://www.sunburyohio.org"
    COUNTRY = "us"
    API_URL = "https://lws-c16afd.webflow.io/service-guidelines/village-of-sunbury"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict[str, dict[str, Any]]] = {"TEST": {}}

    PARAMS = ()

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [wt.GENERAL_WASTE]

    parse = HtmlParser(
        "div.serviceguidelines_highight, div.holiday_cell",
        require=["div.serviceguidelines_highight"],
    )
    preprocess = Compose(_schedule)
    transform = RowTransformer(type_value_map={_WASTE: wt.GENERAL_WASTE})
