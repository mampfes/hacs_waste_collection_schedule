from __future__ import annotations

from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    Schedule,
    SelectExactMatch,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# The council's "When is my bin collected?" page is backed by this public
# ArcGIS layer (one feature per property, carrying the collection weekday,
# zone and recycling frequency).
_LAYER_URL = (
    "https://geoserver.ssc.nsw.gov.au/arcgis/rest/services/WebOnline/MapServer/4"
)

# The GIS layer gives a property's zone but nothing about which fortnight is
# which, so the alternation needs an anchor. This is the Monday of a week the
# council's own Zone 1 calendar highlights yellow (yellow-lid recycling; green
# highlight is the green-lid garden week):
# https://www.sutherlandshire.nsw.gov.au/__data/assets/pdf_file/0020/121934/SSC-Waste-Calendar-2026-27-Zone1-Print.pdf
_ZONE1_RECYCLING_WEEK = date(2026, 8, 31)

# Whole weeks added before taking the parity. Zone 2's recycling week is Zone
# 1's garden week; the two published calendars are opposite on every one of the
# 260 collection days they cover.
_ZONE_WEEK_OFFSETS: dict[str, int] = {"1": 0, "2": 1}

_SCHEDULE_WEEKS = 52


def _sql_quote(value: str) -> str:
    return value.replace("'", "''")


def _where(suburb: str, street: str, house_number: str, **_: Any) -> str:
    # LIKE rather than "=" also covers unit prefixes and spacing quirks.
    address = _sql_quote(f"{str(house_number).strip()} {street.strip()}".upper())
    return (
        f"UPPER(situ1) LIKE '{address}%' "
        f"AND UPPER(situ2) LIKE '{_sql_quote(suburb.upper().strip())}%'"
    )


def _street_where(suburb: str, street: str, **_: Any) -> str:
    return (
        f"UPPER(situ1) LIKE '%{_sql_quote(street.strip().upper())}%'"
        f" AND UPPER(situ2) LIKE '{_sql_quote(suburb.upper().strip())}%'"
    )


def _fortnight_start(first: date, zone: str, target: int) -> date:
    """First collection day on/after ``first`` in a week of the given parity.

    The anchor is a Monday, so flooring the day difference by 7 buckets each
    collection into its own Monday-to-Sunday week. ``target`` 0 is the
    recycling week, 1 the garden week.
    """
    week = (first - _ZONE1_RECYCLING_WEEK).days // 7
    if (week + _ZONE_WEEK_OFFSETS.get(zone, 0)) % 2 != target:
        return first + timedelta(weeks=1)
    return first


def _schedules(
    weekday: int, zone: str, today: date, weekly_recycling: bool
) -> list[Schedule]:
    """Garbage is weekly. Recycling and garden waste alternate fortnights by
    zone; properties flagged for weekly recycling (some unit blocks) get
    recycling every week on top of the fortnightly garden collection."""
    first = recurrence.next_weekday(weekday, on_or_after=today)
    until = today + timedelta(weeks=_SCHEDULE_WEEKS)
    return [
        Schedule("Garbage", first, until=until),
        Schedule(
            "Recycling",
            first if weekly_recycling else _fortnight_start(first, zone, 0),
            recurrence.WEEKLY if weekly_recycling else recurrence.FORTNIGHTLY,
            until=until,
            not_before=first,
        ),
        Schedule(
            "Garden Waste",
            _fortnight_start(first, zone, 1),
            recurrence.FORTNIGHTLY,
            until=until,
            not_before=first,
        ),
    ]


def _describe(attrs: dict, source: BaseSource | None):
    weekday = recurrence.weekday(str(attrs.get("DAY_OF_WEEK", "")).strip())
    if weekday is None:
        raise ValueError(
            f"Unknown collection day {attrs.get('DAY_OF_WEEK')!r} for "
            f"{attrs.get('situ1')}, {attrs.get('situ2')}"
        )
    weekly = str(attrs.get("RECYCLE_PICKUP", "")).strip().lower() == "weekly"
    yield from _schedules(weekday, str(attrs.get("ZONE_NO", "1")), date.today(), weekly)


@final
class Source(BaseSource):
    TITLE = "Sutherland Shire Council"
    DESCRIPTION = "Source for Sutherland Shire Council, NSW, Australia."
    URL = "https://www.sutherlandshire.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "5 Cleveland Place, BONNET BAY": {
            "suburb": "BONNET BAY",
            "street": "Cleveland Place",
            "house_number": "5",
        },
        "20 Waratah Street, CRONULLA": {
            "suburb": "CRONULLA",
            "street": "Waratah Street",
            "house_number": "20",
        },
        # The council's own administration building, and the only Zone 1 case
        # here: both of the above are Zone 2, so nothing exercised the other
        # fortnight.
        "4-20 Eton Street, SUTHERLAND": {
            "suburb": "SUTHERLAND",
            "street": "Eton Street",
            "house_number": "4-20",
        },
    }

    PARAMS = (city("suburb"), street(), house_number())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use the address exactly as it appears on council correspondence, "
            "with the street type spelled out in full (Street, Place, Avenue). "
            "You can check your address on the map at "
            "https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection"
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _LAYER_URL,
        where=_where,
        out_fields="situ1,situ2,DAY_OF_WEEK,ZONE_NO,RECYCLE_PICKUP",
        result_record_count=50,
    )
    parse = ArcGisFeatureParser(
        argument="house_number",
        suggestions=ArcGisDistinctValues(_LAYER_URL, "situ1", where=_street_where),
    )
    preprocess = Compose(
        SelectExactMatch(argument="house_number", key=lambda row: row.get("situ1")),
        RecurrenceExpander(_describe),
        Deduplicate(),
    )
    transform = ICSTransformer(
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
        }
    )
