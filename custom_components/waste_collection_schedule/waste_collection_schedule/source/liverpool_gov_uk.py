import datetime
import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer

# One row per bin with a cell per upcoming date: "Today", "Tomorrow", or
# "Monday, 29th September" without a year.

_parse = date_parsers.nearest_year("%A, %d %B")


def _cell_date(cell: Tag) -> datetime.date:
    text = " ".join(cell.get_text().split())
    today = datetime.date.today()
    if text.startswith("Today"):
        return today
    if text.startswith("Tomorrow"):
        return today + datetime.timedelta(days=1)
    return _parse(re.sub(r"(\d)(st|nd|rd|th)", r"\1", text))


def _row_type(cell: Tag) -> str:
    row = cell.find_parent("tr")
    heading = row.select_one("th") if row is not None else None
    if heading is None:
        # HtmlTransformer turns this into a skipped row.
        raise AttributeError("date cell outside a bin row")
    return heading.get_text(" ", strip=True)


@final
class Source(BaseSource):
    TITLE = "Liverpool City Council"
    DESCRIPTION = "Source for liverpool.gov.uk services for Liverpool City"
    URL = "https://www.liverpool.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "52 Swallowhurst Crescent Liverpool L11 2UZ": {"uprn": "38148233"},
        "1 Aston Street Liverpool L19 8LR": {"uprn": "38010019"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://liverpool.gov.uk/Bins/BinDatesTable",
        params=lambda uprn, **_: {
            "UPRN": uprn,
            "HideGreenBin": "False",
            "ShowTable": "True",
        },
    )
    parse = parsers.HtmlParser("table tr td")
    transform = HtmlTransformer(
        date_getter=_cell_date,
        type_getter=_row_type,
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green": wt.GARDEN_WASTE,
        },
    )
