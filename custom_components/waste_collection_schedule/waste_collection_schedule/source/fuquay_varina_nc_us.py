import re
from datetime import date, datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Fuquay-Varina's Solid_Waste_Information FeatureServer keys one feature per
# address and reports each stream's *next* pickup date as free text (e.g. "The
# next garbage pickup date for this address is Monday, January 06") rather
# than a recurring cadence, so there is nothing for RecurrenceExpander to
# project: preprocess yields the one resolved (date, key) row per stream
# directly, and a plain ICSTransformer types it.

FEATURE_URL = "https://gis1.fuquay-varina.org/server/rest/services/Public/Solid_Waste_Information/MapServer/0"

# ArcGIS field -> waste-type key.
_FIELDS = {
    "garbage_next_pickup_date": "Garbage",
    "recycling_next_pickup_date": "Recycling",
}

_TYPE_MAP = {
    "Garbage": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
}

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_DATE_RE = re.compile(r"([A-Za-z]+),?\s+(\d{1,2})")


def _where(**params) -> str:
    address_query = params["street_address"].strip().lower()
    return f"LOWER(ADDRESS) LIKE '%{address_query}%'"


def _parse_date_from_text(date_text: str) -> date | None:
    """Parse 'The next ... pickup date ... is Monday, January 06' style text."""
    if not date_text:
        return None

    match = _DATE_RE.search(date_text)
    if not match:
        return None

    month = _MONTHS.get(match.group(1).lower())
    if not month:
        return None
    day = int(match.group(2))

    current_date = datetime.now().date()
    current_year = current_date.year
    try:
        pickup_date = date(current_year, month, day)
        # More than 60 days in the past likely means next year's occurrence.
        if (current_date - pickup_date).days > 60:
            pickup_date = date(current_year + 1, month, day)
        return pickup_date
    except ValueError:
        return None


@final
class Source(BaseSource):
    TITLE = "Fuquay-Varina, North Carolina"
    DESCRIPTION = "Source for Fuquay-Varina, NC waste collection via ArcGIS services"
    URL = "https://gis1.fuquay-varina.org/"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"street_address": "155 S Main St"},
        "Test_002": {"street_address": "123 E Vance St"},
    }

    PARAMS = (text_field("street_address", "Street Address"),)

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL,
        where=_where,
        out_fields="garbage_next_pickup_date,recycling_next_pickup_date",
    )
    parse = ArcGisFeatureParser()
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address.strip())

    def preprocess(self, records, source: "Source | None" = None):
        """Turn each matched feature's free-text pickup fields into (date, key) rows.

        Overridden as a method (rather than a shared preprocessor instance)
        because there is no recurring cadence here to hand to
        ``RecurrenceExpander``: each field is already a single resolved "next
        pickup" date, so this is the whole provider-specific projection.
        """
        for attrs in records:
            for field, key in _FIELDS.items():
                pickup_date = _parse_date_from_text(attrs.get(field, ""))
                if pickup_date is not None:
                    yield pickup_date, key
