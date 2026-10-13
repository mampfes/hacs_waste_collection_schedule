from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AspNetPostbackPager import AspNetPostbackPager
from waste_collection_schedule.transformers import HtmlTransformer

# Demonstrates: AspNetPostbackPager (WebForms "next month" postback) +
# EachResponse(HtmlParser) + HtmlTransformer reading the date off the parent cell.


@final
class Source(BaseSource):
    TITLE = "Glasgow City Council"
    DESCRIPTION = "Source for www.glasgow.gov.uk services for Glasgow City Council, UK."
    URL = "https://www.glasgow.gov.uk/"
    COUNTRY = "uk"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "test 1 - house": {"uprn": "906700099060"},
        "test 2 - flat": {"uprn": "906700335412"},
    }

    PARAMS = (uprn(),)

    # The current month plus the next two, so 56-day cycles are covered.
    retrieve = AspNetPostbackPager(
        url=lambda uprn: (
            "https://onlineservices.glasgow.gov.uk/forms/refuseandrecyclingcalendar/"
            f"CollectionsCalendar.aspx?UPRN={uprn}"
        ),
        link_title="Go to the next month",
        pages=2,
    )
    parse = parsers.EachResponse(parsers.HtmlParser("td.CalendarDayStyle img"))

    WASTE_TYPES: ClassVar[list] = [
        wt.GLASS,
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    # The marker's title reads "purple bins are emptied every 56 days"; its
    # parent day cell carries the date ("today is " prefixed for today).
    transform = HtmlTransformer(
        date_getter=lambda el: str(el.find_parent("td")["title"]).replace(
            "today is ", ""
        ),
        type_getter=lambda el: " ".join(str(el["title"]).split()[:2]),
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
        type_value_map={
            "purple bins": wt.GLASS,
            "brown bins": wt.FOOD_WASTE,
            "grey bins": wt.FOOD_WASTE,
            "food waste": wt.FOOD_WASTE,
            "green bins": wt.GENERAL_WASTE,
            "blue bins": wt.RECYCLABLES,
        },
    )
