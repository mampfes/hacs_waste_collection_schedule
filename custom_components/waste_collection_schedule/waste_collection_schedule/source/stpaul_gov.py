"""City of Saint Paul, MN, USA: residential garbage and recycling.

The city's "Garbage & Recycling Day Map" (an ArcGIS Instant App) answers an
address with two polygon layers: the garbage collection weekday (city-wide
organized collection for 1-4 unit dwellings) and the recycling weekday
(Eureka Recycling). The address is located on the city's own tax-parcel layer
(``ArcGis.parcel_centroid``), and both day layers are then queried at that
point (``ArcGisMultiFeatureRetriever``).

Neither layer carries dates. The city's yearly collection calendar states the
rest, which is projected here:

- recycling is collected weekly, garbage weekly or, for residents who chose
  it, every other week (the shaded weeks of the calendar, a single city-wide
  rotation);
- a collection on or after one of the listed holidays in the same week is
  delayed one day (so the Friday route moves to Saturday).

Downtown recycling ("Downtown (Varies)") has no fixed weekday and is left out.
"""

import datetime
import re
from collections.abc import Iterable
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
    parcel_centroid,
)
from waste_collection_schedule.transformers import ICSTransformer

_SERVICES = "https://services1.arcgis.com/9meaaHE3uiba0zr8/arcgis/rest/services"
_PARCELS = f"{_SERVICES}/Saint_Paul_Tax_Parcels/FeatureServer/0"
_GARBAGE_LAYER = f"{_SERVICES}/GarbageCollection/FeatureServer/0"
_RECYCLING_LAYER = f"{_SERVICES}/RecyclingCollection/FeatureServer/0"
_WKID = 102100  # Web Mercator, the parcel layer's spatial reference

_GARBAGE = "Garbage"
_RECYCLING = "Recycling"

# The calendar's shaded "Every Other Week Garbage" weeks run fortnightly from
# the week of 1 January 2026 (Sun 28 Dec 2025 - Sat 3 Jan 2026); this is that
# week's Monday. A fortnightly step from it rather than ISO-week parity, which
# would break across ISO week 53 (28 Dec 2026 - 3 Jan 2027).
_EVERY_OTHER_WEEK_START = datetime.date(2025, 12, 29)
_HORIZON_DAYS = 365

# "Recycling and garbage pick-up will be delayed one day if your collection
# falls on or after the following holidays" (2026 calendar; the 2025 calendar
# also listed the Fourth of July, which falls on a Saturday in 2026). Name
# stems as the ``holidays`` library spells them.
_DELAY_HOLIDAYS = (
    "New Year",
    "Memorial",
    "Juneteenth",
    "Independence",
    "Labor",
    "Thanksgiving",
    "Christmas",
)

# Parcel addresses read "<number> <NAME> <TYPE> [<DIRECTION>]", e.g.
# "1860 REANEY AVE E" or "15 KELLOGG BLVD W".
_DIRECTIONS = {
    "N": "N",
    "S": "S",
    "E": "E",
    "W": "W",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
}
_STREET_TYPES = {
    "AVENUE": "AVE",
    "AVE": "AVE",
    "STREET": "ST",
    "ST": "ST",
    "BOULEVARD": "BLVD",
    "BLVD": "BLVD",
    "ROAD": "RD",
    "RD": "RD",
    "DRIVE": "DR",
    "DR": "DR",
    "LANE": "LN",
    "LN": "LN",
    "PLACE": "PL",
    "PL": "PL",
    "COURT": "CT",
    "CT": "CT",
    "PARKWAY": "PKWY",
    "PKWY": "PKWY",
    "TERRACE": "TER",
    "TER": "TER",
    "CIRCLE": "CIR",
    "CIR": "CIR",
    "TRAIL": "TRL",
    "TRL": "TRL",
    "HIGHWAY": "HWY",
    "HWY": "HWY",
}


def _address_parts(address: Any) -> tuple[str, list[str], str | None, str | None]:
    """Split ``address`` into house number, name words, street type, direction."""
    line = str(address or "").split(",", 1)[0].upper()
    words = re.sub(r"[^0-9A-Z ]", " ", line).split()
    if not words or not words[0][0].isdigit():
        raise SourceArgumentNotFound(
            "address", address, "Start the address with the house number."
        )
    number, *rest = words
    street_type = direction = None
    name: list[str] = []
    for word in rest:
        if word in _DIRECTIONS and (name or direction is None):
            direction = _DIRECTIONS[word]
        elif word in _STREET_TYPES and name:
            street_type = _STREET_TYPES[word]
        else:
            name.append(word)
    if not name:
        raise SourceArgumentNotFound("address", address)
    return number, name, street_type, direction


def _parcel_where(address: Any, **_: Any) -> str:
    number, name, street_type, direction = _address_parts(address)
    clause = f"SiteAddress LIKE '{number} {' '.join(name)} %'"
    if street_type:
        clause += f" AND SiteAddress LIKE '% {street_type}%'"
    if direction:
        clause += f" AND SiteAddress LIKE '% {direction}'"
    return clause


def _similar_where(address: Any, **_: Any) -> str:
    """Addresses on the same street with a nearby house number."""
    number, name, _, _ = _address_parts(address)
    return f"SiteAddress LIKE '{number[:-1]}% {name[0]} %'"


_SIMILAR_ADDRESSES = ArcGisDistinctValues(
    _PARCELS, "SiteAddress", where=_similar_where, limit=50
)


def _describe(
    record: tuple[str, dict], source: BaseSource | None
) -> Iterable[Schedule]:
    layer, attributes = record
    day = attributes.get("DAY" if layer == _GARBAGE else "RECYCLING")
    weekday = recurrence.weekday(str(day or ""))
    if weekday is None:
        # "Downtown (Varies)": no fixed weekday to project.
        return
    today = datetime.date.today()
    this_week = today - datetime.timedelta(days=today.weekday())
    until = today + datetime.timedelta(days=_HORIZON_DAYS)
    every_other_week = layer == _GARBAGE and bool(
        source is not None and source.params.get("every_other_week_garbage")
    )
    if every_other_week:
        start = _EVERY_OTHER_WEEK_START + datetime.timedelta(days=weekday)
        step = recurrence.FORTNIGHTLY
    else:
        start = this_week + datetime.timedelta(days=weekday)
        step = recurrence.WEEKLY
    yield Schedule(layer, start, step, not_before=this_week, until=until)


def _delay_holiday(day: datetime.date) -> bool:
    name = recurrence.us_federal_holidays(day.year, observed=False).get(day, "")
    return any(stem in name for stem in _DELAY_HOLIDAYS)


def _adjust(
    collection_date: datetime.date, key: str, source: BaseSource | None
) -> datetime.date:
    """Delay a collection on or after a listed weekday holiday in its week."""
    monday = collection_date - datetime.timedelta(days=collection_date.weekday())
    for offset in range(collection_date.weekday() + 1):
        if _delay_holiday(monday + datetime.timedelta(days=offset)):
            return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "City of Saint Paul, MN"
    DESCRIPTION = "Source for residential garbage and recycling in Saint Paul, MN, USA."
    URL = "https://www.stpaul.gov/departments/public-works/garbage-and-recycling"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Governor's Residence": {"address": "1006 Summit Ave"},
        "F. Scott Fitzgerald House, every other week": {
            "address": "599 Summit Avenue, Saint Paul, MN 55102",
            "every_other_week_garbage": True,
        },
        "East side, direction left out": {"address": "1860 Reaney Ave"},
        "James J. Hill House, downtown recycling": {"address": "240 Summit Ave"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown house number": {"address": "9999 Summit Ave"},
    }

    PARAMS = (
        street_address(),
        boolean(
            "every_other_week_garbage",
            "Every-other-week garbage collection",
            default=False,
        ),
    )

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address with the house number, e.g. '1006 Summit "
            "Ave' (city, state and ZIP are optional). It is looked up on the "
            "city's Garbage & Recycling Day Map "
            "(https://stpaul.maps.arcgis.com/apps/instant/lookup/index.html?appid=5b3d5ace287e428596cf18fd025fa6fb). "
            "Turn on 'Every-other-week garbage collection' if you chose that "
            "service; garbage is then collected in the weeks shaded on the "
            "city's collection calendar. Downtown recycling has no fixed day "
            "and is not included."
        ),
    }

    retrieve = ArcGisMultiFeatureRetriever(
        [
            (_GARBAGE, _GARBAGE_LAYER, "DAY"),
            (_RECYCLING, _RECYCLING_LAYER, "RECYCLING"),
        ],
        point=parcel_centroid(
            _PARCELS,
            where=_parcel_where,
            argument="address",
            disambiguate_by="SiteAddress",
            out_fields="SiteAddress",
            result_record_count=50,
            wkid=_WKID,
            suggestions=_SIMILAR_ADDRESSES.for_params,
        ),
        in_sr=_WKID,
    )
    parse = ArcGisMultiFeatureParser(first_per_layer=True)
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transform = ICSTransformer(
        type_value_map={_GARBAGE: wt.GENERAL_WASTE, _RECYCLING: wt.RECYCLABLES}
    )
