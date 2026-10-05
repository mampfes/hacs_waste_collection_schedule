import re
from collections.abc import Iterable
from typing import ClassVar, final

from bs4.element import Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import ICSTransformer

API = (
    "https://maps.southderbyshire.gov.uk/iShareLIVE.web/getdata.aspx"
    "?RequestType=LocalInfo&ms=mapsources/MyHouse&format=JSON"
    "&group=Recycling%20Bins%20and%20Waste|Next%20Bin%20Collections"
)

_TYPE_MAP = {
    "Black": wt.GENERAL_WASTE,
    "Green": wt.RECYCLABLES,
    "Brown": wt.GARDEN_WASTE,
}

_COLOURS = re.compile(r"Green|Brown|Black|Podback")
_DATE = re.compile(r"\d{2} \w+ \d{4}")
_parse_date = date_parsers.for_format("%d %B %Y")


def _one_row_per_bin(rounds: list[Tag], source=None) -> Iterable[tuple]:
    """A round's image names its bins ("Green, Brown and Food Waste Bins")."""
    for block in rounds:
        image = block.find("img")
        date = _DATE.search(block.get_text())
        if image is None or date is None:
            continue
        for colour in _COLOURS.findall(str(image.get("alt", ""))):
            yield _parse_date(date.group(0)), colour


@final
class Source(BaseSource):
    TITLE = "South Derbyshire District Council"
    DESCRIPTION = "Source for www.southderbyshire.gov.uk services for South Derbyshire "
    URL = "https://www.southderbyshire.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "test case 1": {"uprn": "100030233745"},
        "test case 2": {"uprn": "10090304958"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(API, params=lambda uprn, **_: {"uid": uprn})

    parse = parsers.HtmlParser(
        "div > div", from_json_key=("Results", "Next_Bin_Collections", "_")
    )

    preprocess = staticmethod(_one_row_per_bin)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
