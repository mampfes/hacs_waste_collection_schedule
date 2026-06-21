import datetime
import logging
from typing import final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service import ArcGis
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

# Shawinigan publishes each collection type as its own ArcGIS MapServer layer.
# A point-in-polygon query against each layer returns a feature whose SCHEDULE /
# SCHEDULETYPE / NAME fields encode the cadence (weekly, bi-weekly with the
# ISO-week parity baked into the SCHEDULE digit, or an explicit list of dates).
# Geocoding happens once in retrieve(); each layer's raw /query Response is paired
# with its metadata so parse() can pull the matched feature and _describe() can
# project concrete dates via the shared RecurrenceExpander.
#
# Public holidays shift or cancel collections. retrieve() also fetches the
# holidays layer (6) and builds a {impact_field: {holiday_date: adjusted_or_None}}
# map, stashed on the source. The pipeline is therefore a Compose of two stages:
# RecurrenceExpander projects each layer's cadence into (date, key) rows, then
# HolidayShift looks up each row's holiday adjustment via _adjust(): the row's
# waste-type key is mapped back to that layer's HOLIDAYFIELD (recorded while
# describing), and the matching holiday map shifts the date forward/back or
# cancels the collection (None). This reproduces the legacy
# `layer_holidays.get(d, d)` + skip-if-None behaviour.

_LOGGER = logging.getLogger(__name__)

TITLE = "Shawinigan"
DESCRIPTION = "Source for Shawinigan, Canada waste collection schedule."
URL = "https://geoweb.shawinigan.ca/CollecteMatieresResiduelles/"
COUNTRY = "ca"

TEST_CASES = {
    "Shawinigan": {"address": "1760 Avenue de la Paix, Shawinigan, QC G9N 6H7"},
}

MAPSERVER_BASE = "https://geoweb.shawinigan.ca/arcgis/rest/services/MunicipalServices_DeTravail/MapServer"

HOLIDAYS_LAYER = 6
DEFAULT_HOLIDAY_FIELD = "IMPACTGARB"

# Each layer: the MapServer layer id and the waste-type string it emits (the
# legacy t= value, keyed into _TYPE_MAP).
LAYERS = [
    {"id": 0, "waste_type": "RECYCLAGE"},  # Blue bin
    {"id": 1, "waste_type": "ORDURES"},  # Grey bin
    {"id": 2, "waste_type": "SAPIN"},  # Christmas tree
    {"id": 3, "waste_type": "FEUILLES"},  # Leaf pickup
    {"id": 4, "waste_type": "COMPOST"},  # Green bin
]

_TYPE_MAP = {
    "RECYCLAGE": RECYCLABLES,
    "ORDURES": GENERAL_WASTE,
    "SAPIN": GARDEN_WASTE,
    "FEUILLES": GARDEN_WASTE,
    "COMPOST": ORGANIC,
}

# Window length used by the legacy weekly/bi-weekly/irregular projection.
HORIZON_DAYS = 365


def _parse_irregular(
    schedule_str: str, start_date: datetime.date, end_date: datetime.date
) -> list[datetime.date]:
    dates = []
    for part in schedule_str.split(","):
        part = part.strip()
        try:
            d = datetime.datetime.strptime(part, "%Y-%m-%d").date()
            if start_date <= d <= end_date:
                dates.append(d)
        except ValueError:
            continue
    return dates


def _parse_biweekly_schedule(
    schedule_str: str, start_date: datetime.date, end_date: datetime.date
) -> list[datetime.date]:
    """Parse a '2 Week' SCHEDULE string like '0001000' or '0020000'.

    The city encodes both the weekday and the ISO-week parity directly in the
    SCHEDULE field. The 7-character string maps positions 0-6 to Sun-Sat; the
    non-zero digit carries the phase:

      digit 1 -> collect on odd  ISO weeks (isocalendar().week % 2 == 1)
      digit 2 -> collect on even ISO weeks (isocalendar().week % 2 == 0)

    Python weekday = (position - 1) % 7 (since position 0 = Sunday = Python 6).
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

    python_weekday = (position - 1) % 7  # 0=Mon ... 6=Sun
    expected_parity = phase % 2  # 1->odd(1), 2->even(0)

    days_ahead = (python_weekday - start_date.weekday()) % 7
    current = start_date + datetime.timedelta(days=days_ahead)

    dates = []
    while current <= end_date:
        if current.isocalendar().week % 2 == expected_parity:
            dates.append(current)
        current += datetime.timedelta(days=7)
    return dates


def _weekly_count(
    weekday: int, start_date: datetime.date, end_date: datetime.date
) -> int:
    """Number of ``weekday`` occurrences in ``[start_date, end_date]`` (inclusive)."""
    days_ahead = (weekday - start_date.weekday()) % 7
    first = start_date + datetime.timedelta(days=days_ahead)
    if first > end_date:
        return 0
    return (end_date - first).days // 7 + 1


def _describe(record, source):
    """Project a layer's matched feature into Schedule descriptors.

    Mirrors the legacy ``_parse_schedule`` branching (irregular list, bi-weekly
    ISO-parity, weekly) while expressing the result through RecurrenceExpander:
    weekly cadence as a single recurring Schedule, and the irregular / bi-weekly
    branches as one-off Schedules (one per concrete date) since neither follows a
    plain fixed-step cadence.

    The record also carries the layer's HOLIDAYFIELD; that is recorded against
    the waste-type key (each layer's type is distinct) so HolidayShift's adjuster
    can find the matching holiday map for the rows this descriptor produces.
    """
    attrs = record["attrs"]
    waste_type = record["waste_type"]
    holiday_field = record["holiday_field"]

    schedule_str = attrs.get("SCHEDULE", "")
    schedule_type = (attrs.get("SCHEDULETYPE") or "").lower()
    day_name = attrs.get("NAME", "")

    if not schedule_str or waste_type is None:
        return

    # Record which holiday impact field governs this layer's rows so _adjust()
    # can pick the right holiday map (the waste-type key is unique per layer).
    if source is not None:
        source._field_for_key[waste_type] = holiday_field

    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=HORIZON_DAYS)
    weekday = recurrence.weekday(day_name)

    # --- Explicit list of dates ("Irregularly") ---
    if "irregularly" in schedule_type or "," in schedule_str:
        for d in _parse_irregular(schedule_str, today, end_date):
            yield Schedule(waste_type, d, recurrence.WEEKLY, 1)
        return

    # --- Bi-weekly: phase encoded in the SCHEDULE digit ---
    if "2" in schedule_type or "bi" in schedule_type:
        biweekly = _parse_biweekly_schedule(schedule_str, today, end_date)
        if biweekly:
            for d in biweekly:
                yield Schedule(waste_type, d, recurrence.WEEKLY, 1)
            return
        # Fallback: SCHEDULE format unexpected, use NAME weekday without phase.
        if weekday is None:
            return
        _LOGGER.warning(
            "Unexpected bi-weekly SCHEDULE %r — falling back to every-other-week",
            schedule_str,
        )
        anchor = recurrence.next_weekday(weekday, on_or_after=today)
        count = (end_date - anchor).days // 14 + 1
        if count > 0:
            yield Schedule(waste_type, anchor, recurrence.FORTNIGHTLY, count)
        return

    # --- Weekly / other periodic ---
    if "week" not in schedule_type or weekday is None:
        return
    count = _weekly_count(weekday, today, end_date)
    if count > 0:
        yield Schedule(
            waste_type,
            recurrence.next_weekday(weekday, on_or_after=today),
            recurrence.WEEKLY,
            count,
        )


def _adjust(collection_date, key, source):
    """Shift or cancel a projected date if it lands on a public holiday.

    Looks up the holiday map for the layer that produced ``key`` (resolved via
    the HOLIDAYFIELD recorded during describe), then mirrors the legacy
    ``layer_holidays.get(d, d)``: an unaffected date passes through unchanged, a
    shifted holiday returns its adjusted date, and a cancelled holiday returns
    ``None`` (HolidayShift drops the row).
    """
    if source is None:
        return collection_date
    field = source._field_for_key.get(key)
    layer_holidays = source._holidays.get(field, {})
    return layer_holidays.get(collection_date, collection_date)


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    TEST_CASES = TEST_CASES
    RAISE_ON_EMPTY = True

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address including city and postal code "
            "(e.g. '1760 Avenue de la Paix, Shawinigan, QC G9N 6H7')."
        ),
    }

    preprocessor = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
        self._address = address.strip()
        # Populated in retrieve(): {impact_field: {holiday_date: adjusted_or_None}}.
        self._holidays: dict[str, dict[datetime.date, datetime.date | None]] = {}
        # Populated in _describe(): {waste_type_key: holiday_field}.
        self._field_for_key: dict[str, str] = {}

    def retrieve(self, source):
        """Geocode once, query each data layer, and load the holiday map.

        Returns a list pairing each data layer's metadata with its raw /query
        Response. The holidays layer (6) is fetched here too and reduced to a
        {field: {holiday_date: adjusted_or_None}} map stashed on the source, so
        HolidayShift's adjuster can apply it after the cadence is projected.
        """
        try:
            location = ArcGis.geocode(self._address, timeout=20)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        self._holidays = self._fetch_holidays()

        results = []
        for layer in LAYERS:
            response = ArcGis.feature_query(
                f"{MAPSERVER_BASE}/{layer['id']}",
                geometry=location,
                out_fields="*",
                timeout=20,
            )
            results.append((layer, response))
        return results

    def parse(self, raw, source):
        """Pull the first matched feature's attributes per layer.

        Yields a record per matched layer carrying the waste-type key, the
        feature attributes and the layer's HOLIDAYFIELD (default "IMPACTGARB").
        Layers whose query matched no feature are skipped.
        """
        for layer, response in raw:
            response.raise_for_status()
            features = response.json().get("features", [])
            if not features:
                continue
            attrs = dict(features[0].get("attributes", {}))
            yield {
                "waste_type": layer["waste_type"],
                "attrs": attrs,
                "holiday_field": attrs.get("HOLIDAYFIELD") or DEFAULT_HOLIDAY_FIELD,
            }

    def _fetch_holidays(self):
        """Fetch the holidays layer and group adjustments by impact field.

        Returns {impact_field: {holiday_date: adjusted_date_or_None}}. Each
        feature's IMPACT* fields carry a coded value from the API domain
        ``piHolidayImpact``:

          "None"       -> no change (skip)
          "OneDayFrwd" -> +1 day
          "TwoDayFrwd" -> +2 days
          "Shift Forw" -> +1 day  (synonym)
          "OneDayBack" -> -1 day
          "Shift Back" -> -1 day  (synonym)
          "Cancel"     -> collection cancelled (mapped to None)
          Others (Next Sat, Prev Sat, ...) -> logged and skipped
        """
        result: dict[str, dict[datetime.date, datetime.date | None]] = {}
        response = ArcGis.feature_query(
            f"{MAPSERVER_BASE}/{HOLIDAYS_LAYER}",
            where="1=1",
            out_fields="*",
            timeout=20,
        )
        response.raise_for_status()
        for feature in response.json().get("features", []):
            attrs = feature.get("attributes", {})
            holiday_ms = attrs.get("HOLIDAYDATE")
            if not holiday_ms:
                continue
            holiday_date = datetime.date.fromtimestamp(holiday_ms / 1000)
            # Iterate over every IMPACT* field — robust to new collection types.
            for field in [k for k in attrs if k.startswith("IMPACT")]:
                val = (attrs.get(field) or "").strip()
                val_lower = val.lower()
                if not val_lower or val_lower == "none":
                    continue
                adjusted: datetime.date | None
                if val_lower == "twodayfrwd":
                    adjusted = holiday_date + datetime.timedelta(days=2)
                elif (
                    "frwd" in val_lower or "forward" in val_lower or "forw" in val_lower
                ):
                    adjusted = holiday_date + datetime.timedelta(days=1)
                elif "back" in val_lower:
                    adjusted = holiday_date - datetime.timedelta(days=1)
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
        return result
