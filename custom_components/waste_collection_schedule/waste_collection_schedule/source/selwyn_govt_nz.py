from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule import Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Selwyn District Council"
DESCRIPTION = (
    "Source for Selwyn District Council kerbside waste collection, New Zealand."
)
URL = "https://www.selwyn.govt.nz/"
COUNTRY = "nz"
TEST_CASES = {
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

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your address exactly as it appears in the address search on "
    "Selwyn District Council's collection days and routes page, e.g. "
    "'30 Tennyson Street Rolleston'."
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the Selwyn District, e.g. "
        "'30 Tennyson Street Rolleston'.",
    }
}

API_URL = (
    "https://gis.selwyn.govt.nz/arcgis/rest/services/SDC_Public/"
    "Refuse_address/MapServer/0/query"
)

# Waste-type labels.
RUBBISH = "Rubbish"
RECYCLING = "Recycling"
ORGANIC = "Organics"

ICON_MAP = {
    RUBBISH: Icons.GENERAL_WASTE,
    RECYCLING: Icons.RECYCLING,
    ORGANIC: Icons.ORGANIC,
}

# Number of weeks of collections to generate.
WEEKS_AHEAD = 8

# Cap the disambiguation suggestions: a prefix match can return many properties.
MAX_SUGGESTIONS = 10

WEEKDAYS = {
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
        return ORGANIC
    return RUBBISH


def _recycling_week(d: date) -> int:
    """Return the council's recycling-cycle week number (1 or 2) for a date.

    Rubbish and organics are collected weekly; only recycling is fortnightly. A
    property's recycling is collected in the weeks whose number equals its
    ``COLLECTION_SCHEDULE``. The week number alternates every 7 days from
    ``RECYCLING_ANCHOR`` -- the same calculation the council's website performs.
    """
    return ((d - RECYCLING_ANCHOR).days // 7) % 2 + 1


class Source:
    def __init__(self, address: str):
        self._address: str = address.strip()

    def fetch(self) -> list[Collection]:
        # Case-insensitive prefix match on the full address. Escape single
        # quotes for the ArcGIS SQL-style ``where`` clause.
        escaped = self._address.lower().replace("'", "''")
        params = {
            "f": "json",
            "where": f"LOWER(Address_full) LIKE '{escaped}%'",
            "outFields": "ChargeType,COLLECTION_SCHEDULE,COLLECTION_DAY,Address_full",
            "returnGeometry": "false",
        }

        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound("address", self._address)

        # A short fragment can match several distinct properties. ArcGIS result
        # ordering is not guaranteed, so don't silently pick one -- if the query
        # is ambiguous, ask the user to disambiguate with the matching addresses.
        matched = sorted({f["attributes"]["Address_full"] for f in features})
        if len(matched) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address", self._address, matched[:MAX_SUGGESTIONS]
            )

        target = matched[0]
        features = [
            f for f in features if f["attributes"].get("Address_full") == target
        ]

        # Collapse the feature rows into one entry per waste-type label. Each
        # property has at most one rubbish, one recycling and one organics charge.
        bins: dict[str, dict] = {}
        for feature in features:
            attrs = feature["attributes"]
            day = (attrs.get("COLLECTION_DAY") or "").strip().lower()
            if day not in WEEKDAYS:
                continue
            label = _label_for_charge(attrs.get("ChargeType", ""))
            schedule = (attrs.get("COLLECTION_SCHEDULE") or "").strip()
            info = bins.setdefault(label, {"weekday": WEEKDAYS[day], "schedule": ""})
            # Only the recycling row carries a meaningful schedule ("1"/"2").
            if schedule in ("1", "2"):
                info["schedule"] = schedule

        if not bins:
            raise SourceArgumentNotFound("address", self._address)

        today = date.today()
        entries: list[Collection] = []
        for offset in range(WEEKS_AHEAD * 7):
            day = today + timedelta(days=offset)
            for label, info in bins.items():
                if day.weekday() != info["weekday"]:
                    continue
                # Rubbish and organics are weekly; recycling is fortnightly and
                # only falls in the weeks matching the property's schedule.
                if label == RECYCLING:
                    schedule = info["schedule"]
                    if schedule not in ("1", "2"):
                        continue
                    if _recycling_week(day) != int(schedule):
                        continue
                entries.append(Collection(day, label, ICON_MAP[label]))

        return entries
