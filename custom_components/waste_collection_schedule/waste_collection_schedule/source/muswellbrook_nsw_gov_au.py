import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Each zone page has one .waste-block per bin: its title ("Recycling (Yellow
# lid)"), how often it is collected ("... is collected fortnightly.") and the
# next collection (<time datetime="2026-10-14T00:00:00+00:00">). The dates of
# the coming year are projected from that, and a collection falling on
# Christmas Day moves to Boxing Day. An unknown zone answers 404 with a page
# without any .waste-block.

COLLECTION_URL = "https://www.muswellbrook.nsw.gov.au/waste-collection/zone-{}/"
LOOKAHEAD = datetime.timedelta(weeks=52)


def _describe(block, source):
    title = block.select_one(".waste-block__title")
    often = block.select_one(".waste-block__often")
    time = block.select_one(".waste-block__time")
    if title is None or often is None or time is None:
        return
    try:
        next_date = datetime.date.fromisoformat(time.get("datetime", "")[:10])
    except ValueError:
        return
    step = (
        recurrence.WEEKLY
        if "weekly" in often.get_text(strip=True).lower()
        else recurrence.FORTNIGHTLY
    )
    yield Schedule(
        title.get_text(strip=True),
        next_date,
        step,
        until=datetime.date.today() + LOOKAHEAD,
    )


def _boxing_day(collection_date, key, source):
    if (collection_date.month, collection_date.day) == (12, 25):
        return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "Muswellbrook Shire Council"
    DESCRIPTION = "Source for Muswellbrook Shire Council, NSW, Australia."
    URL = "https://www.muswellbrook.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Zone 3A": {"zone": "3a"},
        "Zone 5B": {"zone": "5b"},
        "Zone 1B": {"zone": "1b"},
    }

    PARAMS = (
        text_field("zone", "Zone", coerce=lambda value: str(value).strip().lower()),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your collection zone at "
            "https://www.muswellbrook.nsw.gov.au/waste-collection/ and enter it as "
            "e.g. '3a' or '5b'."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda zone, **_: COLLECTION_URL.format(zone))
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser(".waste-block"),
        argument="zone",
        contains="waste-block",
        hint="valid zones are 1a, 1b, 2a, 2b, 3a, 3b, 4a, 4b, 5a and 5b",
    )
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_boxing_day))
    transform = ICSTransformer(
        type_value_map={
            "General Waste (Red lid)": wt.GENERAL_WASTE,
            "Recycling (Yellow lid)": wt.RECYCLABLES,
            "Garden Waste (Green lid)": wt.GARDEN_WASTE,
        },
    )
