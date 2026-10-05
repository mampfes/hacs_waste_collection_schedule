import json
from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.transformers import HtmlTransformer


def _mylocation(uprn, **_) -> dict[str, str]:
    """The council site reads the property from a ``mylocation`` JSON cookie."""
    location = {
        "postcode": "",
        "myaddress": "",
        "uprn": str(uprn),
        "usrn": "",
        "ward": "",
        "parish": "",
        "lng": 0,
        "lat": 0,
    }
    return {"mylocation": quote(json.dumps(location, separators=(",", ":")))}


def _kind(img) -> str | None:
    """The bin an icon stands for, from its title (or alt) text."""
    title = (img.get("title") or img.get("alt") or "").lower()
    if "refuse" in title or "black" in title:
        return "Refuse"
    if "recycling" in title or "blue" in title or "lid" in title:
        return "Recycling"
    if "garden" in title or "brown" in title:
        return "Garden"
    if "food" in title or "caddy" in title:
        return "Food"
    return None


def _date(img) -> str:
    """The "Thursday 1 October:" heading of the day this icon sits under."""
    heading = img.find_parent("div").find("h3", class_="collectiondate")
    return heading.get_text(strip=True).rstrip(":").strip()


@final
class Source(BaseSource):
    TITLE = "Hinckley & Bosworth Borough Council"
    DESCRIPTION = "Source for Hinckley & Bosworth Borough Council."
    URL = "https://www.hinckley-bosworth.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_House": {"uprn": "100030499851"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    retrieve = retrievers.Request(
        "https://www.hinckley-bosworth.gov.uk/collections",
        cookies=_mylocation,
    )

    # One heading per collection day, followed by one icon per bin.
    parse = parsers.HtmlParser(
        ".first_date_bins img, .last_date_bins img",
        require=[".first_date_bins, .last_date_bins"],
    )

    preprocess = RowFilter(lambda img, source: _kind(img) is not None)

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_kind,
        parse_date=date_parsers.nearest_year("%A %d %B"),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        },
    )
