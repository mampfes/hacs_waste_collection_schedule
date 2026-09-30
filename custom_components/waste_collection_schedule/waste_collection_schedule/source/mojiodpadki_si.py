import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import ICSTransformer

URL_SCHEDULES = "https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov"

# The badge text of each tag in a day cell.
_TAG_TYPES = {
    "MKO": wt.GENERAL_WASTE,
    "EMB": wt.RECYCLABLES,
    "BIO": wt.ORGANIC,
    "PAP": wt.PAPER,
}


def _days(tables, source):
    """One (date, tag) row per waste tag in each day cell of the month tables.

    Each table is one month. Its header names the month and, on the first table
    of a year only, the year; a table without one continues the previous year.
    """
    year = datetime.date.today().year
    for table in tables:
        year_cell = table.select_one("thead td.year")
        found = year_cell.get_text(strip=True) if year_cell else ""
        if found.isdigit():
            year = int(found)
        month_cell = table.select_one("thead td.month")
        month = (
            recurrence.month(month_cell.get_text(strip=True)) if month_cell else None
        )
        if month is None:
            continue
        for tag in table.select("tbody span.tag"):
            row = tag.find_parent("tr")
            day = row.select_one("td.day-number") if row else None
            if day is None or not day.get_text(strip=True).isdigit():
                continue
            yield (
                datetime.date(year, month, int(day.get_text(strip=True))),
                tag.get_text(strip=True),
            )


@final
class Source(BaseSource):
    TITLE = "Moji odpadki, Ljubljana"
    DESCRIPTION = "Source script for mojiodpadki.si"
    URL = "https://www.mojiodpadki.si"
    COUNTRY = "si"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "DrzavniZbor": {"uprn": "1049"},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search your address at "
            "https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov. The UPRN "
            "is the last part of the address of the schedule page "
            "(`.../urniki-odvoza-odpadkov/s/<uprn>`)."
        ),
    }

    retrieve = Request(
        lambda uprn, **_: f"{URL_SCHEDULES}/s/{uprn}",
    )

    parse = HtmlParser("table.calendar")
    preprocess = staticmethod(_days)
    transform = ICSTransformer(type_value_map=_TAG_TYPES)
