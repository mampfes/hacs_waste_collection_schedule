import re
from typing import final
from urllib.parse import urlencode

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import HtmlTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

# Demonstrates: the OCAPI "myarea" two-step flow (address lookup -> geolocation
# id -> waste services) via TwoStepRetriever, and HtmlParser(from_json_key=...)
# for the wasteservices response, which is HTML rendered inside a JSON field.
# Dozens of AU councils share this OCAPI platform.

BASE = "https://www.yarraranges.vic.gov.au"
SEARCH_URL = f"{BASE}/api/v1/myarea/search"
WASTE_URL = f"{BASE}/ocapi/Public/myarea/wasteservices"

_DATE_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")

_TYPE_MAP = {
    "Rubbish Collection": GENERAL_WASTE,
    "Recycling Collection": RECYCLABLES,
    "New weekly FOGO collection": ORGANIC,
}


def _geolocation_id(lookup, source) -> str:
    items = lookup.json().get("Items") or []
    if not items:
        raise SourceArgumentNotFound(
            "street_address",
            source.params.get("street_address"),
            "address search returned no results.",
        )
    return items[0]["Id"]


def _waste_type(article: Tag) -> str:
    # The heading carries the service name. Skip the "Burning off" notice and any
    # heading-less article by raising, which HtmlTransformer treats as "skip row".
    heading = article.h3
    waste_type = heading.string.strip() if heading and heading.string else ""
    if not waste_type or waste_type == "Burning off":
        raise ValueError("no collectable waste type")
    return waste_type


def _next_date(article: Tag) -> str | None:
    # The next collection date is embedded in free text inside .next-service.
    # Return None (skip the row) when the block or a date is absent.
    next_service = article.find("div", {"class": "next-service"})
    if next_service is None:
        return None
    match = _DATE_RE.search(next_service.get_text())
    return match.group(1) if match else None


@final
class Source(BaseSource):
    TITLE = "Yarra Ranges Council"
    DESCRIPTION = "Source for Yarra Ranges Council rubbish collection."
    URL = "https://www.yarraranges.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES = [GENERAL_WASTE, RECYCLABLES, ORGANIC]

    TEST_CASES = {
        "Petstock Lilydale": {
            "street_address": "5/447-449 Maroondah Highway Lilydale 3140"
        },
        "Beechworth Bakery Healesville": {
            "street_address": "316 Maroondah Highway Healesville 3777"
        },
    }

    PARAMS = [text_field("street_address", label="Street Address")]

    HOWTO = {
        "en": "Enter your full street address as it appears on the council's "
        "waste collection lookup page (street, suburb and postcode).",
    }

    retrieve = retrievers.TwoStepRetriever(
        lookup_url=lambda street_address=None, **_: (
            f"{SEARCH_URL}?" + urlencode({"keywords": street_address})
        ),
        extract=_geolocation_id,
        schedule_url=lambda key, **_: (
            f"{WASTE_URL}?" + urlencode({"geolocationid": key, "ocsvclang": "en-AU"})
        ),
        headers={"Accept": "application/json"},
    )

    parse = parsers.HtmlParser(
        "article", from_json_key="responseContent", require=["article"]
    )

    parse_date = date_parsers.for_format("%d/%m/%Y")

    transform = HtmlTransformer(
        date_getter=_next_date,
        type_getter=_waste_type,
        type_value_map=_TYPE_MAP,
        parse_date=parse_date,
    )

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address)
