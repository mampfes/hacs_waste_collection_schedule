import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import ICSTransformer

# One letter per bin in a day cell's class (e.g. "GPOC"): Green, Brown, Purple,
# blue (C), Orange (glass container).
_BIN_TYPES = {
    "G": wt.GENERAL_WASTE,
    "B": wt.GARDEN_WASTE,
    "P": wt.RECYCLABLES,
    "C": wt.PAPER,
    "O": wt.GLASS,
}


def _days(records, source):
    """One (date, bin letter) row per bin collected on a marked day.

    ``records`` is the page title (naming the year) followed by one container
    per month, whose header names the month and whose day cells carry the bins
    collected that day as their class.
    """
    year = None
    for record in records:
        if "title_txt" in (record.get("class") or []):
            found = re.search(r"\d{4}", record.get_text())
            year = int(found.group(0)) if found else None
            continue
        if year is None:
            continue
        header = record.select_one(".month-header")
        month = recurrence.month(header.get_text(strip=True)) if header else None
        if month is None:
            continue
        for cell in record.select(".days-container > div"):
            bins = "".join(cell.get("class") or [])
            if not bins or not set(bins) <= set(_BIN_TYPES):
                continue
            day = cell.get_text(strip=True)
            if not day.isdigit():
                continue
            for letter in bins:
                yield datetime.date(year, month, int(day)), letter


@final
class Source(BaseSource):
    TITLE = "Moray Council"
    DESCRIPTION = "Source for Moray Council, UK."
    URL = "https://moray.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"id": "00013734"},
        "Test_002": {"id": 60216},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ]

    PARAMS = (
        text_field("id", "Property ID", coerce=lambda value: str(value).zfill(8)),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your address in the Moray Council bin day finder "
            "(https://bindayfinder.moray.gov.uk). The property id is the `id` "
            "in the address of your calendar page "
            "(`cal_<year>_view.php?id=<id>`); leading zeros may be left out."
        ),
    }

    retrieve = Request(
        lambda **_: (
            "https://bindayfinder.moray.gov.uk/"
            f"cal_{datetime.date.today().year}_view.php"
        ),
        params=lambda id, **_: {"id": id},
    )

    parse = HtmlParser(".title_txt, div.month-container")
    preprocess = staticmethod(_days)
    transform = ICSTransformer(type_value_map=_BIN_TYPES)
