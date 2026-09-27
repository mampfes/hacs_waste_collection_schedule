import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.JaduBinCollections import strip_ordinal
from waste_collection_schedule.transformers import RowTransformer

_parse = date_parsers.nearest_year("%a %d %b")


def _date(text: str) -> datetime.date:
    """ "Tue 29th Sep", "Today" or "Tomorrow"."""
    today = datetime.date.today()
    lowered = text.strip().lower()
    if lowered == "today":
        return today
    if lowered == "tomorrow":
        return today + datetime.timedelta(days=1)
    return _parse(strip_ordinal(text))


@final
class Source(BaseSource):
    TITLE = "North West Leicestershire District Council"
    DESCRIPTION = "Source for www.nwleics.gov.uk services for the city of North West Leicestershire District Council, UK"
    URL = "https://nwleics.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dunmore": {"uprn": "10002359002"},
        "Station Road": {"uprn": 100030573554},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://my.nwleics.gov.uk/location",
        params=lambda uprn, **_: {
            "put": f"nwl{uprn}",
            "rememberme": "0",
            "redirect": "/",
        },
    )
    parse = parsers.HtmlLabelledDates(
        "ul.refuse li",
        label="a",
        date="strong.date",
        parse_date=_date,
    )
    transform = RowTransformer(
        type_value_map={
            "Garden Waste": wt.GARDEN_WASTE,
            "Red Box": wt.RECYCLABLES,
            "Blue Bag": wt.PAPER,
            "Yellow Bag": wt.RECYCLABLES,
            "Black Bin": wt.GENERAL_WASTE,
            "Black Sack": wt.GENERAL_WASTE,
            "Food Waste": wt.FOOD_WASTE,
        },
    )
