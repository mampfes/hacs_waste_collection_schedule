from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule import Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Selwyn District Council"
DESCRIPTION = (
    "Source for Selwyn District Council kerbside waste collection, New Zealand."
)
URL = "https://www.selwyn.govt.nz/"
TEST_CASES = {
    "30 Tennyson Street Rolleston": {"address": "30 Tennyson Street Rolleston"},
    "77 Gerald Street Lincoln": {"address": "77 Gerald Street Lincoln"},
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

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _label_for_charge(charge_type: str) -> str:
    """Map a raw ``ChargeType`` value to a collapsed waste-type label.

    Selwyn bills several weekly red-bin variants ("refuse uniform charge",
    "rubbish 80 litre", "rubbish 240 litre", ...). They are all the same weekly
    rubbish collection, so they collapse to a single label.
    """
    charge = charge_type.lower()
    if charge == "recycling":
        return RECYCLING
    if charge == "organic":
        return ORGANIC
    return RUBBISH


def _fortnight_parity(d: date) -> int:
    """Return a stable, Monday-aligned fortnight parity (0/1) for a date.

    Anchored to the proleptic-Gregorian epoch (ordinal 1 is a Monday), so the
    parity is continuous across year boundaries. This avoids the off-by-one that
    raw ISO week numbers introduce in 53-week ISO years (e.g. 2026), where the
    week number would otherwise repeat its parity across the New Year.
    """
    return ((d.toordinal() - 1) // 7) % 2


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
            "outFields": "ChargeType,COLLECTION_FREQUENCY,COLLECTION_SCHEDULE,"
            "COLLECTION_DAY,Address_full",
            "returnGeometry": "false",
        }

        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        features = r.json().get("features", [])
        if not features:
            raise SourceArgumentNotFound("address", self._address)

        # A short fragment can match several properties; keep only the rows that
        # belong to the first (closest) matched address.
        target = features[0]["attributes"]["Address_full"]
        features = [
            f for f in features if f["attributes"].get("Address_full") == target
        ]

        # Collapse the feature rows into one entry per waste-type label.
        bins: dict[str, dict] = {}
        for feature in features:
            attrs = feature["attributes"]
            day = (attrs.get("COLLECTION_DAY") or "").strip().lower()
            if day not in WEEKDAYS:
                continue
            label = _label_for_charge(attrs.get("ChargeType", ""))
            frequency = (attrs.get("COLLECTION_FREQUENCY") or "").strip().lower()
            schedule = (attrs.get("COLLECTION_SCHEDULE") or "").strip()
            bins[label] = {
                "weekday": WEEKDAYS[day],
                "fortnightly": frequency.startswith("fortnight"),
                "schedule": schedule,
            }

        if not bins:
            raise SourceArgumentNotFound("address", self._address)

        today = date.today()
        entries: list[Collection] = []
        for offset in range((WEEKS_AHEAD * 7) + 1):
            day = today + timedelta(days=offset)
            for label, info in bins.items():
                if day.weekday() != info["weekday"]:
                    continue
                if info["fortnightly"]:
                    if not self._collected_this_fortnight(label, info["schedule"], day):
                        continue
                entries.append(Collection(day, label, ICON_MAP[label]))

        return entries

    @staticmethod
    def _collected_this_fortnight(label: str, schedule: str, day: date) -> bool:
        """Resolve whether a fortnightly bin is collected on ``day``.

        Recycling and organics alternate on the same weekday. ``COLLECTION_SCHEDULE``
        ("1" or "2") selects which of the two master calendars a property follows;
        the absolute phase is anchored from the council's published calendar
        (verified: a schedule-"2" property collects organics in even fortnights).
        """
        if schedule not in ("1", "2"):
            # Phase cannot be determined for this property; emit nothing rather
            # than guess. (Residential properties always carry "1" or "2".)
            return False
        even = _fortnight_parity(day) == 0
        organics_week = even if schedule == "2" else not even
        return organics_week if label == ORGANIC else not organics_week
