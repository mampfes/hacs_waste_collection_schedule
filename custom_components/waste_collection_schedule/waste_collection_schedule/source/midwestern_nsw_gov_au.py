import calendar
import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import JsonTransformer

# The council's calendar API answers one date range per request with a record
# per collection day (weekday, date and the bins collected). Every area of the
# same side of the region shares the calendars, so the area only picks which
# calendars to ask for and which weekday's records to keep. A year of schedule
# is twelve monthly requests, one response each.

_API_URL = "https://www.midwestern.nsw.gov.au/ocapi/calendars/getcalendaritems"
_MONTHS = 12

_MONDAY_THURSDAY_IDS = [
    "cf9dcec1-4072-4068-8080-d494837dc275",
    "ec2967b5-b13e-41a9-8f83-2e988f67fc6a",
    "a2c28b3f-5e53-4c7b-8c8a-045dc1e16fb2",
    "ae79f069-472e-4ec1-9a9b-bd7c0bf45ae2",
]
_TUESDAY_WEDNESDAY_IDS = [
    "b3a2a212-edb8-44cf-a306-21d4e4c1be81",
    "649f4490-eed3-44e3-a5ab-cf747b0fccc8",
    "cc86a639-87ce-4347-a10c-e5fea9059e24",
    "1ab0e286-d710-436f-8086-c8051fc267f7",
]
_FRIDAY_IDS = [
    "938a1031-73fe-4f38-a660-22982cc2678c",
    "5bf0474c-11a8-48de-a052-493335024b33",
    "e8ee40eb-40a7-463c-b761-d46194565780",
    "5284d0b5-9d5a-446c-b2fc-6c0868aabfd3",
]

# area -> (collection weekday, calendar ids)
_AREAS = {
    "mudgee_north_monday": ("Monday", _MONDAY_THURSDAY_IDS),
    "mudgee_north_thursday": ("Thursday", _MONDAY_THURSDAY_IDS),
    "mudgee_south_tuesday": ("Tuesday", _TUESDAY_WEDNESDAY_IDS),
    "mudgee_south_wednesday": ("Wednesday", _TUESDAY_WEDNESDAY_IDS),
    "gulgong_monday": ("Monday", _MONDAY_THURSDAY_IDS),
    "gulgong_thursday": ("Thursday", _MONDAY_THURSDAY_IDS),
    "kandos_rylstone_friday": ("Friday", _FRIDAY_IDS),
}


def _months(_source, _context) -> list[tuple[str, str]]:
    """``(first day, last day)`` of each of the next twelve months."""
    today = datetime.date.today()
    months = []
    for offset in range(_MONTHS):
        index = today.month - 1 + offset
        year, month = today.year + index // 12, index % 12 + 1
        last = calendar.monthrange(year, month)[1]
        months.append(
            (
                datetime.date(year, month, 1).isoformat(),
                datetime.date(year, month, last).isoformat(),
            )
        )
    return months


def _body(month, _context, *, area, **_) -> dict:
    start, end = month
    return {
        "LanguageCode": "en-AU",
        "StartDate": start,
        "EndDate": end,
        "Ids": _AREAS[area][1],
    }


def _is_area_weekday(day, source) -> bool:
    return day.get("Day") == _AREAS[source.params["area"]][0]


@final
class Source(BaseSource):
    TITLE = "Mid-Western Regional Council"
    DESCRIPTION = "Source for Mid-Western Regional Council waste collection schedules."
    URL = "https://www.midwestern.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mudgee North Monday": {"area": "mudgee_north_monday"},
        "Mudgee North Thursday": {"area": "mudgee_north_thursday"},
        "Mudgee South Tuesday": {"area": "mudgee_south_tuesday"},
        "Mudgee South Wednesday": {"area": "mudgee_south_wednesday"},
        "Gulgong Monday": {"area": "gulgong_monday"},
        "Gulgong Thursday": {"area": "gulgong_thursday"},
        "Kandos/Rylstone Friday": {"area": "kandos_rylstone_friday"},
    }

    PARAMS = (dropdown("area", list(_AREAS), label="Collection area"),)

    retrieve = retrievers.FanOutRetriever(
        targets=_months,
        fetch=retrievers.Request(_API_URL, method="POST", json=_body),
    )
    parse = parsers.EachResponse(
        parsers.JsonParser("data", expected_values={"success": True})
    )
    preprocess = preprocessors.Compose(
        preprocessors.RowFilter(_is_area_weekday),
        preprocessors.ExplodeList("Items", into="item"),
    )
    transform = JsonTransformer(
        date_key="Date",
        type_key=lambda record: record["item"].get("Name", "").strip(),
        type_value_map={
            "LANDFILL": wt.GENERAL_WASTE,
            "FOOD AND GARDEN": wt.ORGANIC,
            "RECYCLING": wt.RECYCLABLES,
            "PAPER AND CARDBOARD": wt.PAPER,
        },
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
