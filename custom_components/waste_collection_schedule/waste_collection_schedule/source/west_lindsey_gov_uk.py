from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "BLACK": wt.GENERAL_WASTE,
    "BLUE": wt.RECYCLABLES,
    "PURPLE": wt.PAPER,
    "GREEN": wt.GARDEN_WASTE,
    "ORANGE": wt.FOOD_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "West Lindsey District Council"
    DESCRIPTION = "Source for West Lindsey District Council, Lincolnshire, UK."
    URL = "https://www.west-lindsey.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"x": 509762, "y": 384493, "id": 919},
        "Test_002": {"x": "511918", "y": "401495", "id": "39713"},
        "Test_003": {"x": 482566, "y": 390375, "id": 16636},
    }

    PARAMS = (
        text_field("x", "Easting", coerce=str),
        text_field("y", "Northing", coerce=str),
        text_field("id", "Property ID", coerce=str),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your bin collection day on "
            "https://www.west-lindsey.gov.uk/bins-waste-recycling/find-your-bin-collection-day "
            "with the browser's Developer Tools open on the Network tab. Once the "
            "schedule is shown, look at the last few requests: one has a payload "
            "line `query: x=482566;y=390375;id=16636`. Use those three numbers "
            "as x (the 6-figure Easting), y (the 6-figure Northing) and id (the "
            "property id)."
        ),
    }

    retrieve = retrievers.Request(
        "https://wlnk.statmap.co.uk/map/Cluster.svc/getpage",
        params=lambda x, y, id, **_: {
            "script": r"\Cluster\Cluster.AuroraScript$",
            "taskId": "bins",
            "format": "js",
            "updateOnly": "true",
            "query": f"x={x};y={y};id={id}",
        },
        headers={
            "user-agent": "Mozilla/5.0",
            "referer": "https://www.west-lindsey.gov.uk/",
        },
        # The page is a JavaScript file whose HTML sits in an escaped string
        # literal (<, \", \r\n): unescape it so the markup can be parsed.
        encoding="unicode-escape",
    )

    parse = parsers.HtmlLabelledDates(
        "li.auroraListItem li",
        label="span",
        date=":scope",
        date_pattern=r"(\d{1,2}/\d{1,2})",
        all_dates=True,
    )

    transform = RowTransformer(
        parse_date=date_parsers.DateParserNextWeekday("%d/%m"),
        type_value_map=_TYPE_MAP,
    )
