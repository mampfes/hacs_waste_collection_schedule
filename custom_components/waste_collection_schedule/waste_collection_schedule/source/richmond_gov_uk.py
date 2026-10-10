import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer

# The "My Richmond" page lists one <h4> per service inside div.my-waste, each
# followed by a <ul> whose first <li> holds the next date ("Tuesday 13 October
# 2026", optionally followed by a "View calendar" link). A property without a
# garden waste contract shows "No collection contract at this address" there
# instead, which is skipped. An unknown UPRN gets a page without div.my-waste.

API_URL = "https://www.richmond.gov.uk/my_richmond"

_DATE = re.compile(r"(\d{1,2} \w+ \d{4})\s*$")


def _next_date(heading):
    items = heading.find_next_sibling("ul")
    item = items.find("li") if items else None
    if item is None:
        return None
    # Only the <li>'s own text: the date, without the text of its links.
    text = " ".join(item.find_all(string=True, recursive=False)).strip()
    if "No collection contract" in text:
        return None
    match = _DATE.search(text)
    return match.group(1) if match else None


@final
class Source(BaseSource):
    TITLE = "London Borough of Richmond upon Thames"
    DESCRIPTION = "Source for London Borough of Richmond upon Thames"
    URL = "https://www.richmond.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Sheen Common Drive": {"uprn": "100022316011"},
        "Rosemont Road": {"uprn": "100022315214"},
        "Bryanston Avenue": {"uprn": "100022330653"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Get your Unique Property Reference Number (UPRN) by going to "
            "<https://www.findmyaddress.co.uk/> and entering your address details."
        ),
    }

    retrieve = HttpGetRetriever(
        url=API_URL, params=lambda uprn, **_: {"pid": str(uprn)}
    )
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("div.my-waste h4"),
        argument="uprn",
        contains="my-waste",
    )
    transform = HtmlTransformer(
        date_getter=_next_date,
        type_getter=lambda heading: heading.get_text(strip=True),
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            # One round: the food caddy goes out with the rubbish.
            "Rubbish and food": wt.GENERAL_WASTE,
            "Glass, can, plastic and carton recycling": wt.RECYCLABLES,
            "Paper and card recycling": wt.PAPER,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
