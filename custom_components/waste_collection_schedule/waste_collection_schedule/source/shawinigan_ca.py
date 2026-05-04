"""Source for Shawinigan, Canada waste collection schedule.

Uses ArcGIS REST API with spatial queries to determine collection districts
based on address coordinates, then extracts collection schedules from districts.
"""

import logging
from datetime import date, datetime, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    epoch_ms_to_date,
    geocode,
    query_feature_layer,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Shawinigan"
DESCRIPTION = "Source for Shawinigan, Canada waste collection schedule."
URL = "https://geoweb.shawinigan.ca/CollecteMatieresResiduelles/"
COUNTRY = "CA"

TEST_CASES = {
    "Shawinigan": {"address": "1760 Avenue de la Paix, Shawinigan, QC G9N 6H7"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address including city and postal code (e.g., '1760 Avenue de la Paix, Shawinigan, QC G9N 6H7')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

# Layer IDs for collection types
LAYERS = {
    0: {"type": "RECYCLAGE", "icon": "mdi:recycle"},  # Blue Bin Pickup
    1: {"type": "ORDURES", "icon": "mdi:trash-can"},  # Grey Bin Pickup
    # Christmas Tree Collection
    2: {"type": "SAPIN", "icon": "mdi:pine-tree"},
    3: {"type": "FEUILLES", "icon": "mdi:leaf-maple"},  # Leaf Pickup
    4: {"type": "COMPOST", "icon": "mdi:leaf"},  # Green Bin Pickup
}

MAPSERVER_BASE = "https://geoweb.shawinigan.ca/arcgis/rest/services/MunicipalServices_DeTravail/MapServer"
HOLIDAYS_LAYER = 6

_WEEKDAY_MAP = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        """Fetch waste collection schedule for the specified address."""
        try:
            location = geocode(self._address, timeout=20)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        today = date.today()
        end_date = today + timedelta(days=365)

        # Step 1: fetch all raw layer attributes
        raw_layers: dict[int, dict] = {}
        for layer_id in LAYERS:
            try:
                features = query_feature_layer(
                    f"{MAPSERVER_BASE}/{layer_id}",
                    geometry=location,
                    out_fields="*",
                )
                if features:
                    raw_layers[layer_id] = features[0]
            except ArcGisError:
                _LOGGER.debug("No data for layer %d", layer_id)

        if not raw_layers:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: (no-op — bi-weekly phase is read directly from the SCHEDULE digit)

        # Step 3: fetch holidays per impact field
        all_holidays = _get_holidays_by_field()

        # Step 4: generate Collection entries
        entries: list[Collection] = []
        for layer_id, attrs in raw_layers.items():
            layer_info = LAYERS[layer_id]
            schedule_str = attrs.get("SCHEDULE", "")
            schedule_type = attrs.get("SCHEDULETYPE", "").lower()
            day_name = attrs.get("NAME", "")
            holiday_field = attrs.get("HOLIDAYFIELD") or "IMPACTGARB"
            layer_holidays = all_holidays.get(holiday_field, {})
            description = attrs.get("DESCRIPT") or None

            collection_dates = _parse_schedule(
                schedule_str,
                schedule_type,
                day_name,
                today,
                end_date,
            )
            for d in collection_dates:
                adjusted = layer_holidays.get(d, d)
                if adjusted is None:
                    continue  # Collection cancelled due to holiday
                entries.append(
                    Collection(
                        date=adjusted,
                        t=layer_info["type"],
                        icon=layer_info["icon"],
                        description=description,
                    )
                )

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return sorted(entries, key=lambda x: x.date)


# ---------------------------------------------------------------------------
# Module-level helpers (stateless, easy to unit-test)
# ---------------------------------------------------------------------------


def _weekday_num(day_name: str) -> int:
    return _WEEKDAY_MAP.get((day_name or "").strip().lower(), -1)


def _parse_irregular(schedule_str: str, start_date: date, end_date: date) -> list[date]:
    dates = []
    for part in schedule_str.split(","):
        part = part.strip()
        try:
            d = datetime.strptime(part, "%Y-%m-%d").date()
            if start_date <= d <= end_date:
                dates.append(d)
        except ValueError:
            continue
    return dates


def _parse_biweekly_schedule(
    schedule_str: str, start_date: date, end_date: date
) -> list[date]:
    """Parse a '2 Week' SCHEDULE string like '0001000' or '0020000'.

    The city encodes both the weekday and the ISO-week parity directly in the
    SCHEDULE field.  The 7-character string maps positions 0-6 to Sun-Sat; the
    non-zero digit in the string carries the phase:

      digit 1 → collect on odd  ISO weeks  (isocalendar().week % 2 == 1)
      digit 2 → collect on even ISO weeks  (isocalendar().week % 2 == 0)

    Python weekday = (position - 1) % 7  (since position 0 = Sunday = Python 6).

    Edge case: when a year has ISO week 53 (e.g. 2026), two consecutive matching
    weekdays can share the same parity, yielding an extra entry.  This is rare
    and matches the city's own web-app behaviour.
    """
    if len(schedule_str) != 7:
        return []

    position = -1
    phase = 0
    for i, c in enumerate(schedule_str):
        if c in ("1", "2"):
            position = i
            phase = int(c)
            break

    if position < 0:
        return []

    python_weekday = (position - 1) % 7  # 0=Mon … 6=Sun
    expected_parity = phase % 2  # 1→odd(1), 2→even(0)

    days_ahead = (python_weekday - start_date.weekday()) % 7
    current = start_date + timedelta(days=days_ahead)

    dates = []
    while current <= end_date:
        if current.isocalendar().week % 2 == expected_parity:
            dates.append(current)
        current += timedelta(days=7)
    return dates


def _parse_schedule(
    schedule_str: str,
    schedule_type: str,
    day_name: str,
    start_date: date,
    end_date: date,
    exclude_dates: dict | None = None,  # kept for backward compatibility; unused
) -> list[date]:
    """Parse a Shawinigan MapServer SCHEDULE field and return collection dates.

    For bi-weekly ('2 Week') layers the SCHEDULE string encodes both the weekday
    and the ISO-week parity (digit 1 = odd weeks, digit 2 = even weeks), so no
    cross-layer calibration is needed.

    ``exclude_dates`` is accepted but ignored (preserved for test compatibility).
    """
    if not schedule_str:
        return []

    schedule_type = (schedule_type or "").lower()
    weekday = _weekday_num(day_name)

    # --- Explicit list of dates ("Irregularly") ---
    if "irregularly" in schedule_type or "," in schedule_str:
        return _parse_irregular(schedule_str, start_date, end_date)

    # --- Bi-weekly: phase encoded in SCHEDULE digit ---
    if "2" in schedule_type or "bi" in schedule_type:
        result = _parse_biweekly_schedule(schedule_str, start_date, end_date)
        if result:
            return result
        # Fallback: SCHEDULE format unexpected, use NAME weekday without phase
        if weekday < 0:
            return []
        _LOGGER.warning(
            "Unexpected bi-weekly SCHEDULE %r — falling back to every-other-week from start",
            schedule_str,
        )
        days_ahead = (weekday - start_date.weekday()) % 7
        anchor = start_date + timedelta(days=days_ahead)
        out = []
        current = anchor
        while current <= end_date:
            out.append(current)
            current += timedelta(days=14)
        return out

    # --- Weekly / other periodic ---
    if "week" not in schedule_type or weekday < 0:
        return []

    days_ahead = (weekday - start_date.weekday()) % 7
    dates = []
    current = start_date + timedelta(days=days_ahead)
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=7)
    return dates


def _get_holidays_by_field() -> dict[str, dict[date, date | None]]:
    """Return holiday adjustments grouped by impact field name.

    Maps holiday_date -> adjusted_date, or None when the collection is
    cancelled.  query_feature_layer already unwraps the 'attributes' dict.

    Actual coded values from the API domain ``piHolidayImpact``:
      "None"       -> no change (skip entry)
      "OneDayFrwd" -> +1 day
      "TwoDayFrwd" -> +2 days
      "Shift Forw" -> +1 day  (synonym used by the city)
      "OneDayBack" -> -1 day
      "Shift Back" -> -1 day  (synonym)
      "Cancel"     -> collection cancelled (mapped to None)
      Others (Next Sat, Prev Sat, Next Sun, Prev Sun) -> logged and skipped
    """
    result: dict[str, dict[date, date | None]] = {}
    try:
        features = query_feature_layer(
            f"{MAPSERVER_BASE}/{HOLIDAYS_LAYER}",
            where="1=1",
            out_fields="*",
        )
        for attrs in features:  # attrs is already the attributes dict
            holiday_ms = attrs.get("HOLIDAYDATE")
            if not holiday_ms:
                continue
            holiday_date = epoch_ms_to_date(holiday_ms)
            # Iterate over all IMPACT* fields dynamically — robust against new collection types
            impact_fields = [k for k in attrs if k.startswith("IMPACT")]
            for field in impact_fields:
                val = (attrs.get(field) or "").strip()
                val_lower = val.lower()
                if not val_lower or val_lower == "none":
                    continue
                if val_lower == "twodayfrwd":
                    adjusted: date | None = holiday_date + timedelta(days=2)
                elif (
                    "frwd" in val_lower or "forward" in val_lower or "forw" in val_lower
                ):
                    adjusted = holiday_date + timedelta(days=1)
                elif "back" in val_lower:
                    adjusted = holiday_date - timedelta(days=1)
                elif val_lower == "cancel":
                    adjusted = None
                else:
                    _LOGGER.debug(
                        "Unhandled holiday impact code %r for %s on %s",
                        val,
                        field,
                        holiday_date,
                    )
                    continue
                result.setdefault(field, {})[holiday_date] = adjusted
    except ArcGisError:
        _LOGGER.debug("Could not fetch holidays")
    return result
