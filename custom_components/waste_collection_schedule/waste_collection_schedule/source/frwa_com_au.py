import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import HtmlTransformer

HOME = "https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads"
AJAX = "https://fleurieuregionalwasteauthority.com.au/wp-admin/admin-ajax.php"
HEADERS = {"Referer": HOME}


def _pick_nonce(response, **_) -> str:
    """The page embeds the WordPress ajax nonce as ``"ajax_nonce":"<token>"``."""
    match = re.search(r'"ajax_nonce"\s*:\s*"([^"]+)"', response.text)
    if not match:
        raise ValueError("Unable to find ajax_nonce on the FRWA website")
    return match.group(1)


def _pick_property_id(response, nonce, name_or_number, street, district, **_) -> str:
    """Take the hit whose number matches and whose label holds street and district."""
    number = str(name_or_number).upper()
    street_name = street.upper()
    district_name = district.upper()
    found = None
    for item in response.json():
        label = item["label"]
        if (
            number == item["street_no"]
            and street_name in label
            and district_name in label
        ):
            found = item["id"]
    if found is None:
        raise SourceArgumentNotFound(
            "street", f"{number} {street_name} in {district_name}"
        )
    return found


def _next_date(block) -> str | None:
    for row in block.select("table tr"):
        cells = row.find_all("td")
        if cells and cells[0].get_text(strip=True) == "Next Collection Date:":
            return cells[1].get_text(strip=True)
    return None


@final
class Source(BaseSource):
    TITLE = "Fleurieu Regional Waste Authority"
    DESCRIPTION = "Source script for fleurieuregionalwasteauthority.com.au"
    URL = "https://fleurieuregionalwasteauthority.com.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region("Kangaroo Island Council", url="https://www.kangarooisland.sa.gov.au"),
        region(
            "District Council of Yankalilla", url="https://www.yankalilla.sa.gov.au"
        ),
        region("City of Victor Harbor", url="https://www.victor.sa.gov.au"),
        region("Alexandrina Council", url="https://www.alexandrina.sa.gov.au"),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Victor Harbor": {
            "name_or_number": "42",
            "street": "WISHART CRESCENT",
            "district": "ENCOUNTER BAY",
        },
        "Yankalilla": {
            "name_or_number": "12",
            "street": "Wallman Street",
            "district": "Yankalilla",
        },
        "Kangaroo Island": {
            "name_or_number": "3",
            "street": "Flinders Grove",
            "district": "Island Beach",
        },
        "Alexandrina": {
            "name_or_number": "10",
            "street": "Jacobs Street",
            "district": "Goolwa South",
        },
    }

    PARAMS = (
        house_number("name_or_number"),
        street("street"),
        district("district"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit [FRWA collection calendar]"
            "(https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads) "
            "and search for your street. Use the name/number, street name and "
            "district name as they appear when your collection schedule is "
            "being displayed."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(HOME, headers=HEADERS, pick=_pick_nonce),
            retrievers.Lookup(
                AJAX,
                headers=HEADERS,
                params=lambda nonce, name_or_number, street, **_: {
                    "term": f"{str(name_or_number).upper()} {street.upper()}",
                    "action": "autocomplete_search",
                    "security": nonce,
                },
                pick=_pick_property_id,
            ),
        ),
        url=AJAX,
        method="POST",
        headers=HEADERS,
        params=lambda nonce, property_id, **_: {
            "id": property_id,
            "action": "fetch_bin_collection",
        },
    )

    parse = parsers.HtmlParser("div.coll-main-wrap")

    transform = HtmlTransformer(
        date_getter=_next_date,
        type_getter=lambda block: (
            block.find("h6").get_text(strip=True).split(" Collection")[0]
        ),
        type_value_map={
            "Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green Waste": wt.GARDEN_WASTE,
        },
        parse_date=date_parsers.for_format("%d %B %Y"),
    )
