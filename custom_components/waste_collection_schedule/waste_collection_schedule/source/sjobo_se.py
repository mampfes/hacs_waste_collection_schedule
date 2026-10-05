import datetime
from typing import ClassVar, final
from urllib.parse import urlencode

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address
from waste_collection_schedule.transformers import HtmlTransformer

API = "https://webbservice.indecta.se/kunder/sjobo/kalender/basfiler/onlinekalender.php"

# The calendar page is a table per month; each day is a small table with the day
# number in a `styleDayHit` cell and one empty cell per collection, whose class
# is the bin code. A code ending in `-H` is the same bin in a holiday week.
_BIN_TEXT = {
    "FF1": "Matavfall, restavfall, metallförpackningar och tidningar",
    "FF2": (
        "Pappersförpackningar, plastförpackningar (hårda & mjuka), ofärgade och "
        "färgade glasförpackningar samt batterier och ljuskällor i batteriboxen"
    ),
    "MoR": "Matavfall och Restavfall",
    "FG": "Färgade glasförpackningar",
    "OFG": "Ofärgade glasförpackningar",
    "RST": "Restavfall",
    "KOM": "Kompost",
    "MAT": "Matavfall",
    "MEF": "Metallförpackningar",
    "PAF": "Pappersförpackningar",
    "PLF": "Plastförpackningar (hårda och mjuka)",
    "ToP": "Tidningar och Papper",
    "TRG": "Trädgårdsavfall",
}

# FF1, FF2 and MoR each combine several waste types in one bin.
_TYPE_MAP = {
    _BIN_TEXT["FF1"]: wt.OTHER,
    _BIN_TEXT["FF2"]: wt.OTHER,
    _BIN_TEXT["MoR"]: wt.OTHER,
    _BIN_TEXT["FG"]: wt.GLASS,
    _BIN_TEXT["OFG"]: wt.GLASS,
    _BIN_TEXT["RST"]: wt.GENERAL_WASTE,
    _BIN_TEXT["KOM"]: wt.ORGANIC,
    _BIN_TEXT["MAT"]: wt.FOOD_WASTE,
    _BIN_TEXT["MEF"]: wt.RECYCLABLES,
    _BIN_TEXT["PAF"]: wt.PAPER,
    _BIN_TEXT["PLF"]: wt.RECYCLABLES,
    _BIN_TEXT["ToP"]: wt.PAPER,
    _BIN_TEXT["TRG"]: wt.GARDEN_WASTE,
}

_MARKER = ", ".join(f"td.{code}, td.{code}-H" for code in _BIN_TEXT)


def _code(cell: Tag) -> str:
    return next(c for c in cell["class"] if c.removesuffix("-H") in _BIN_TEXT)


def _date(cell: Tag) -> datetime.date:
    """The date of the day table the marker cell sits in."""
    month_table = cell.find_parent("table", {"class": "styleMonth"})
    month_name, year = month_table.find("td", {"class": "styleMonthName"}).text.split(
        " - "
    )
    day_table = cell.find_parent("table")
    day_cell = day_table.find("td", {"class": "styleDayHit"}) or day_table.find(
        "td", {"style": "styleDayHit"}
    )
    # The first day of each week also carries a week-number label (`v.2`) in the
    # same cell, so read the day from the div holding just the digits.
    day = next(
        div.get_text(strip=True)
        for div in reversed(day_cell.find_all("div"))
        if div.get_text(strip=True).isdigit()
    )
    return datetime.date(int(year), recurrence.month(month_name) or 0, int(day))


@final
class Source(BaseSource):
    TITLE = "Sjöbo kommun"
    DESCRIPTION = "Source for Sjöbo kommun waste collection."
    URL = "https://www.sjobo.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kommunhuset": {"address": "Gamla torg 10", "city": "Sjöbo"},
    }

    PARAMS = (street_address("address"), city("city"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and city as they appear in the calendar "
            "search on https://www.sjobo.se. Collections in a holiday week are "
            "marked 'Helgvecka' in the description."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url=lambda address, city, **_: (
            f"{API}?" + urlencode({"hsG": address, "hsO": city}, encoding="iso-8859-1")
        ),
    )
    parse = parsers.HtmlParser(_MARKER)
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda cell: _BIN_TEXT[_code(cell).removesuffix("-H")],
        description_getter=lambda cell: (
            "Helgvecka" if _code(cell).endswith("-H") else None
        ),
        type_value_map=_TYPE_MAP,
    )
