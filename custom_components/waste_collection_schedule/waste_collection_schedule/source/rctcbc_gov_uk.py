from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _date(pickup: Tag) -> str:
    """The day number of the card holding this pickup, with its calendar's month."""
    card = pickup.find_parent("div", class_="card-body")
    wrap = pickup.find_parent("div", class_="calendar-wrap")
    day = card.select_one(".card-title") if card else None
    month = wrap.select_one(".calendar-month") if wrap else None
    if day is None or month is None:
        raise ValueError("pickup outside a dated calendar card")
    return f"{day.get_text(strip=True)} {month.get_text(strip=True)}"


@final
class Source(BaseSource):
    TITLE = "Rhondda Cynon Taf County Borough Council"
    DESCRIPTION = "Source for rctcbc.gov.uk services for Rhondda Cynon Taf County Borough Council, Wales, UK"
    URL = "https://www.rctcbc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10024274791"},
        "Test_002": {"uprn": "100100718352"},
        "Test_003": {"uprn": 100100733093},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by searching for your address on "
            "[Find My Address](https://www.findmyaddress.co.uk/)."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    # The page carries a printable calendar of the next three months whichever
    # ``month`` is requested, so the first page holds the whole schedule.
    retrieve = HttpGetRetriever(
        url="https://www.rctcbc.gov.uk/EN/Resident/RecyclingandWasteServices/Findyourrecyclingandwastecollectionday.aspx",
        params=lambda uprn, **_: {"uprn": str(uprn), "month": 0},
    )
    parse = parsers.HtmlParser(".printableCalendar .calendar-wrap .card-body-padding a")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda a: a.get_text(strip=True),
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Black Bags": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
