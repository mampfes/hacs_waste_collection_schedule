import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://cms.northnorthants.gov.uk/bin-collection-search/calendarevents"
_ROUNDS = (
    ("recycling", "Recycling"),
    ("garden", "Garden"),
    ("refuse", "Refuse"),
    ("food", "Food"),
)


def _calendar_url(uprn, **_) -> str:
    """The calendar for the next six weeks."""
    today = datetime.date.today()
    until = today + datetime.timedelta(days=42)
    return f"{_API_URL}/{uprn}/{today:%Y-%m-%d}/{until:%Y-%m-%d}"


def _round(event) -> str:
    """The round an event's container belongs to: "Empty CBC Bin Recycling 240l"."""
    title = event["title"].lower()
    for keyword, name in _ROUNDS:
        if keyword in title:
            return name
    return event["title"]


def _epoch_ms(event) -> str:
    """The milliseconds inside a .NET ``/Date(1790809199000)/`` stamp."""
    return "".join(filter(str.isdigit, event["start"]))


@final
class Source(BaseSource):
    TITLE = "North Northamptonshire council"
    DESCRIPTION = "Source for North Northamptonshire council."
    URL = "https://www.northnorthants.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100030987513": {"uprn": 100030987513},
        "100030987514": {"uprn": 100030987514},
        "10093005361": {"uprn": "10093005361"},
        "Castle Farm House Main Street Rockingham North Northamptonshire LE16 8TG": {
            "uprn": "100030993903"
        },
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(url=_calendar_url)
    parse = parsers.JsonParser(raise_for_status=True)
    transform = JsonTransformer(
        date_key=_epoch_ms,
        type_key=_round,
        parse_date=date_parsers.from_epoch("ms"),
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Refuse": wt.GENERAL_WASTE,
            "Food": wt.FOOD_WASTE,
        },
    )
