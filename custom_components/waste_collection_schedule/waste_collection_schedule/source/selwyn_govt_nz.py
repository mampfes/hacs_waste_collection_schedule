from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Selwyn's ArcGIS layer is queried with an address-prefix `where` clause (a
# single ArcGisFeatureRetriever), which fits declaratively. What doesn't fit a
# plain ArcGisFeatureParser is the legacy disambiguation behaviour: a short
# prefix can match several distinct properties, so the response must be
# inspected for ambiguity (with an exact-match fallback and suggestions) before
# the matched rows are aggregated into a per-waste-type weekday/cadence. That
# extra logic is expressed as a `parse`-method override, same technique as
# cm_lisboa_pt.py. Once the per-property weekday + cadence is known, dates are
# projected via the shared RecurrenceExpander rather than a hand-rolled
# day-by-day loop.

FEATURE_URL = (
    "https://gis.selwyn.govt.nz/arcgis/rest/services/SDC_Public/"
    "Refuse_address/MapServer/0"
)

# Waste-type keys emitted by _describe -> canonical WasteType.
RUBBISH = "Rubbish"
RECYCLING = "Recycling"
ORGANICS = "Organics"

_TYPE_MAP = {
    RUBBISH: GENERAL_WASTE,
    RECYCLING: RECYCLABLES,
    ORGANICS: ORGANIC,
}

# Number of weeks of collections to generate (matches the legacy default).
WEEKS_AHEAD = 8

# Cap the disambiguation suggestions: a prefix match can return many properties.
MAX_SUGGESTIONS = 10

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Reference date for the council's two-weekly recycling cycle: a "week 1" Sunday.
# Matches the anchor used by the council's own collection-day look-up widget.
RECYCLING_ANCHOR = date(2024, 3, 17)


def _label_for_charge(charge_type: str) -> str:
    """Map a raw ``ChargeType`` value to a collapsed waste-type label.

    Selwyn bills several weekly red-bin variants ("refuse uniform charge",
    "rubbish 80 litre", "rubbish 240 litre", ...). They are all the same weekly
    rubbish collection, so they collapse to a single label.
    """
    charge = charge_type.strip().lower()
    if charge == "recycling":
        return RECYCLING
    if charge == "organic":
        return ORGANICS
    return RUBBISH


def _recycling_week(d: date) -> int:
    """Return the council's recycling-cycle week number (1 or 2) for a date."""
    return ((d - RECYCLING_ANCHOR).days // 7) % 2 + 1


def _where(address: str, **_: Any) -> str:
    escaped = address.lower().replace("'", "''")
    return f"LOWER(Address_full) LIKE '{escaped}%'"


def _describe(bins: dict, source):
    # Bound the projection to the same fixed [today, today + WEEKS_AHEAD*7)
    # window the legacy day-by-day loop used, rather than a fixed occurrence
    # count, so a fortnightly recycling cadence and the weekly streams cover
    # exactly the same span.
    window_end = date.today() + timedelta(days=WEEKS_AHEAD * 7 - 1)
    for label, info in bins.items():
        start = recurrence.next_weekday(info["weekday"])
        if label == RECYCLING:
            schedule = info["schedule"]
            if schedule not in ("1", "2"):
                continue
            if _recycling_week(start) != int(schedule):
                start += timedelta(weeks=1)
            yield Schedule(label, start, recurrence.FORTNIGHTLY, until=window_end)
        else:
            yield Schedule(label, start, recurrence.WEEKLY, until=window_end)


@final
class Source(BaseSource):
    TITLE = "Selwyn District Council"
    DESCRIPTION = (
        "Source for Selwyn District Council kerbside waste collection, New Zealand."
    )
    URL = "https://www.selwyn.govt.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        # schedule 1 (Friday), with organics
        "30 Tennyson Street Rolleston": {"address": "30 Tennyson Street Rolleston"},
        # schedule 2 (Monday), with organics
        "77 Gerald Street Lincoln": {"address": "77 Gerald Street Lincoln"},
        # schedule 1 (Tuesday), with organics
        "15 Meijer Drive Lincoln": {"address": "15 Meijer Drive Lincoln"},
        # schedule 1 (Thursday), with organics
        "22 Mclaughlins Road Darfield": {"address": "22 Mclaughlins Road Darfield"},
        # schedule 2 (Monday), no organics service
        "156 Leeston Road Springston": {"address": "156 Leeston Road Springston"},
    }

    PARAMS = (text_field("address", "Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as it appears in the address search on "
            "Selwyn District Council's collection days and routes page, e.g. "
            "'30 Tennyson Street Rolleston'."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL,
        where=_where,
        out_fields="ChargeType,COLLECTION_SCHEDULE,COLLECTION_DAY,Address_full",
    )
    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())

    def parse(self, response, source: "Source | None" = None) -> list[dict]:
        address = self.params["address"]
        features = ArcGisFeatureParser()(response, source)
        if not features:
            raise SourceArgumentNotFound("address", address)

        # A short fragment can match several distinct properties. ArcGIS result
        # ordering is not guaranteed, so don't silently pick one. If the user's
        # input is itself an exact (case-insensitive) full address, use it even
        # when other properties share it as a prefix; otherwise ask the user to
        # disambiguate with the matching addresses.
        matched: list[str] = sorted(
            {f["Address_full"] for f in features if f.get("Address_full")}
        )
        if len(matched) > 1:
            exact = [a for a in matched if a.lower() == address.lower()]
            if not exact:
                raise SourceArgAmbiguousWithSuggestions(
                    "address", address, matched[:MAX_SUGGESTIONS]
                )
            target = exact[0]
        else:
            target = matched[0]
        features = [f for f in features if f.get("Address_full") == target]

        # Collapse the feature rows into one entry per waste-type label. Each
        # property has at most one rubbish, one recycling and one organics charge.
        bins: dict[str, dict] = {}
        for attrs in features:
            day = (attrs.get("COLLECTION_DAY") or "").strip().lower()
            if day not in _WEEKDAYS:
                continue
            label = _label_for_charge(attrs.get("ChargeType", ""))
            schedule = (attrs.get("COLLECTION_SCHEDULE") or "").strip()
            info = bins.setdefault(label, {"weekday": _WEEKDAYS[day], "schedule": ""})
            # Only the recycling row carries a meaningful schedule ("1"/"2").
            if schedule in ("1", "2"):
                info["schedule"] = schedule

        if not bins:
            raise SourceArgumentNotFound("address", address)

        return [bins]
