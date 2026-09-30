import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import HtmlTransformer


def _date_text(img) -> str:
    """Day number of the cell plus the month heading of the calendar it sits in."""
    day = img.find_parent("td").find("span").get_text(strip=True)
    month = img.find_parent("div", class_="cldr_month").find("h2").get_text(strip=True)
    return f"{day} {month}"


def _bin_type(img) -> str:
    """The round named by the marker's ``cldr_img_<round>`` class."""
    for cls in img.get("class", []):
        found = re.fullmatch(r"cldr_img_(recycling|refuse|garden)", cls)
        if found:
            return found.group(1)
    return ""


@final
class Source(BaseSource):
    TITLE = "Borough Council of King's Lynn & West Norfolk"
    DESCRIPTION = "Source for www.west-norfolk.gov.uk services for Borough Council of King's Lynn & West Norfolk, UK."
    URL = "https://www.west-norfolk.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100090969937"},
        "Test_002": {"uprn": "100090989776"},
        "Test_003": {"uprn": "10000021270"},
        "Test_004": {"uprn": 100090969937},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering in your address details."
        ),
    }

    # The calendar page reads the household from the ``bcklwn_uprn`` cookie
    # (zero-padded to 12 digits).
    retrieve = Request(
        "https://www.west-norfolk.gov.uk/bincollectionscalendar",
        cookies=lambda uprn, **_: {"bcklwn_uprn": str(uprn).zfill(12)},
    )
    # One marker image per collection inside each day cell of the month grids.
    parse = HtmlParser(
        "div.cldr_month td.recycling img, "
        "div.cldr_month td.refuse img, "
        "div.cldr_month td.garden img"
    )
    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_bin_type,
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "refuse": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
        },
    )
