import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    WeekdayRecurrence,
)
from waste_collection_schedule.transformers import ICSTransformer


def _thanksgiving(year: int) -> datetime.date:
    """The 4th Thursday of November."""
    first = datetime.date(year, 11, 1)
    return recurrence.next_weekday(3, on_or_after=first) + datetime.timedelta(weeks=3)


def _holiday_shift(collection_date: datetime.date, key: str, source) -> datetime.date:
    """Per the county's holiday policy, a collection on or after Thanksgiving or
    Christmas in the same Monday-Sunday week moves one day forward for each."""
    week_start = collection_date - datetime.timedelta(days=collection_date.weekday())
    for holiday in (
        _thanksgiving(collection_date.year),
        datetime.date(collection_date.year, 12, 25),
    ):
        if week_start <= holiday <= collection_date:
            collection_date += datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "Orange County, FL"
    DESCRIPTION = "Source for Orange County Government curbside collection schedules."
    URL = "https://ocarcims.ocfl.net/"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@rbusquet"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Orange County Fire Station 27": {"parcel_id": "012128690001243"},
    }

    PARAMS = (
        text_field("parcel_id", "Parcel ID", coerce=lambda value: str(value).strip()),
    )

    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your address at https://ocarcims.ocfl.net/ or "
            "https://www.ocpafl.org/. The 15-digit parcel ID appears in the "
            "search results on either site."
        ),
    }

    retrieve = retrievers.Request(
        "https://ocarcims.ocfl.net/Home.aspx",
        params=lambda parcel_id, **_: {"ParcelID": parcel_id},
    )
    # One cell per service, holding its weekday; the label is the cell before it.
    parse = parsers.HtmlParser(
        "#Curbside_PickupResultsUpdatePanel td.pickupRows:not(.resultHeader)",
        require=["#Curbside_PickupResultsUpdatePanel"],
    )
    preprocess = Compose(
        WeekdayRecurrence(
            day=lambda cell: cell.get_text(" ", strip=True),
            keys=lambda cell: cell.find_previous_sibling("td").get_text(
                " ", strip=True
            ),
        ),
        HolidayShift(_holiday_shift),
    )
    transform = ICSTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Recycle": wt.RECYCLABLES,
            "Yard Waste": wt.GARDEN_WASTE,
            "Bulk": wt.BULKY_WASTE,
            "Large Item": wt.BULKY_WASTE,
        },
        carry_raw_label=True,
    )
