import re
from datetime import datetime
from typing import final
from urllib.parse import urlencode

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
    preserved,
    resolve,
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
        "article", from_json_key="responseContent", shape=["article"]
    )

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address)

    def classify(self, record) -> Collection | None:
        heading = record.h3
        waste_type = heading.string.strip() if heading and heading.string else ""
        if not waste_type or waste_type == "Burning off":
            return None

        next_service = record.find("div", {"class": "next-service"})
        if next_service is None:
            return None
        match = _DATE_RE.search(next_service.get_text())
        if not match:
            return None

        date = datetime.strptime(match.group(1), "%d/%m/%Y").date()
        return Collection(
            date=date,
            waste_type=_TYPE_MAP.get(waste_type)
            or resolve(waste_type)
            or preserved(waste_type),
        )
