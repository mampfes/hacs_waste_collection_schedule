import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.AshfordCollectionDay import (
    CollectionDayRetriever,
)
from waste_collection_schedule.transformers import HtmlTransformer


def _label(cell) -> str:
    """The bin name without its container note, "Recycling (green bin / ...)"."""
    return cell.find("b").get_text(strip=True).split("(")[0].strip()


def _date(cell) -> datetime.date | str | None:
    """The next date: "Friday 09/10/2026", or "Today" on the collection day.

    A service with no date (garden waste not subscribed to, large items) shows
    none, so its cell yields nothing.
    """
    span = cell.find("span", id=re.compile(r"CollectionDayLookup2_Label_\w*_Date"))
    text = span.get_text(strip=True) if span else ""
    if text.lower() == "today":
        return datetime.date.today()
    if " " not in text:
        return None
    return text.split(" ")[1]


@final
class Source(BaseSource):
    TITLE = "Ashford Borough Council"
    DESCRIPTION = "Source for Ashford Borough Council."
    URL = "https://ashford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "100060796052": {"uprn": 100060796052, "postcode": "TN23 3DY"},
        "100060780440": {"uprn": "100060780440", "postcode": "TN24 9JD"},
        "100062558476": {"uprn": "100062558476", "postcode": "TN233LX"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the UPRN of your property. You can find "
            "your UPRN at https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = CollectionDayRetriever()
    parse = parsers.HtmlParser("td[id*=CollectionDayLookup2_td_]")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Household Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
