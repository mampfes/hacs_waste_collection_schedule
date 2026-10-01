import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import HtmlTransformer

_LID = re.compile(r"\s*-\s*\w+-lid bin\s*$", re.IGNORECASE)


def _next_collection(block) -> str:
    """The date cell following the "Next Collection:" label."""
    for row in block.select("tr"):
        cells = row.select("td")
        if len(cells) == 2 and "next collection" in cells[0].get_text().lower():
            return cells[1].get_text(strip=True)
    return ""


@final
class Source(BaseSource):
    TITLE = "North Adelaide Waste Management Authority"
    DESCRIPTION = (
        "Source for nawma.sa.gov.au (Salisbury, Playford, and Gawler South Australia)."
    )
    URL = "https://www.nawma.sa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "128 Bridge Road": {
            "street_number": "128",
            "street_name": "Bridge Road",
            "suburb": "Pooraka",
        },  # Monday
        "226 Bridge Road": {
            "street_number": "226",
            "street_name": "Bridge Road",
            "suburb": "Pooraka",
        },  # Monday reverse
        "Whites Road": {"street_name": "Whites Road", "suburb": "Paralowie"},  # Tuesday
        "Hazel Avenue": {
            "street_name": "Hazel Avenue",
            "suburb": "Angle Vale",
        },  # Wednesday
        "155 Murray St": {
            "street_name": "Murray Street (sec between Ayers and the railway line",
            "suburb": "Gawler",
        },  # Thursday
        "Edward Crescent": {
            "street_name": "Edward Crescent",
            "suburb": "Evanston Park",
        },  # Friday
    }

    PARAMS = (
        house_number("street_number", optional=True),
        street("street_name"),
        city("suburb"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street, suburb and optionally the house number as they "
            "appear on the [NAWMA collection day lookup](https://www.nawma.sa.gov.au/)."
        ),
    }

    retrieve = HttpPostRetriever(
        url="https://www.nawma.sa.gov.au/wp-admin/admin-ajax.php",
        data=lambda street_name, suburb, street_number=None, **_: {
            "action": "collection_day",
            "street_no": street_number or "",
            "street": street_name,
            "area": suburb,
            "pid": "2444",
        },
    )
    parse = parsers.HtmlParser("div.coll-content")
    transform = HtmlTransformer(
        date_getter=_next_collection,
        type_getter=lambda block: block.select_one("h6").get_text(strip=True),
        clean=lambda label: _LID.sub("", label),
        type_value_map={
            "general household waste": wt.GENERAL_WASTE,
            "household recycling": wt.RECYCLABLES,
            "food organics and garden organics (fogo)": wt.ORGANIC,
        },
    )
