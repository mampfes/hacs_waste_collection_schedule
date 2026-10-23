import datetime
import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.mijnafvalwijzer.nl/nl"

_YEAR_ID = re.compile(r"^jaar-(\d{4})$")


def _date(entry: Tag) -> datetime.date:
    """The collection date: "dinsdag 13 oktober" inside its "jaar-2026" block."""
    _weekday, day, month = entry.select_one("span.span-line-break").get_text().split()
    year = entry.find_parent("div", id=_YEAR_ID).get("id")[-4:]
    return datetime.date(int(year), recurrence.month(month), int(day))


@final
class Source(BaseSource):
    TITLE = "Afval Wijzer"
    DESCRIPTION = "Source for all cities regions supported in mijnafvalwijzer.nl"
    URL = "https://www.mijnafvalwijzer.nl"
    COUNTRY = "nl"

    # An unknown address answers 404; an address without collections would
    # otherwise look like an empty calendar.
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Eindhoven1": {"postcode": "5651AN", "number": "34", "add": "A"},
        "Eindhoven2": {"postcode": "5651AN", "number": "34"},
        "Meierijstad": {"postcode": "5481LR", "number": "6"},
        "Rotterdam": {"postcode": "3067AL", "number": "53"},
    }

    PARAMS = (
        postcode(house_field="number"),
        text_field("add", "House Number Addition", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the same postcode, house number and (optional) addition "
            "as for your home address at https://www.mijnafvalwijzer.nl/"
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.HttpGetRetriever(
        url=lambda postcode=None, number=None, add=None, **_: (
            f"{API_URL}/{(postcode or '').replace(' ', '')}"
            f"/{(number or '').replace(' ', '')}/{(add or '').replace(' ', '')}"
        ),
    )

    parse = parsers.ArgumentGuard(
        parsers.HtmlParser(
            "div.block.md\\:hidden div.ophaaldagen a.wasteInfoIcon",
            require=["div.block.md\\:hidden div.ophaaldagen"],
        ),
        argument="postcode",
        contains="ophaaldagen",
        hint="use the postcode, house number and addition of your home address",
    )

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda entry: entry.select_one("span.afvaldescr").get_text(),
        type_value_map={
            "Restafval": wt.GENERAL_WASTE,
            "Papier en karton": wt.PAPER,
            "GFT": wt.ORGANIC,
            "Groente, Fruit en Tuinafval": wt.ORGANIC,
            "Groente-, fruit- en etensresten + tuinafval": wt.ORGANIC,
            "PMD": wt.RECYCLABLES,
            "Plastic, Metalen en Drankkartons": wt.RECYCLABLES,
        },
    )
