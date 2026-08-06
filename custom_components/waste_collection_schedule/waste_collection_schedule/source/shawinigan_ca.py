import datetime
import logging
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisHolidayShift,
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Shawinigan publishes each collection type as its own ArcGIS MapServer layer.
# A point-in-polygon query against each layer returns a feature whose SCHEDULE /
# SCHEDULETYPE / NAME fields encode the cadence (weekly, bi-weekly with the
# ISO-week parity baked into the SCHEDULE digit, or an explicit list of dates).
# The shared multi-layer retriever geocodes once and queries every layer; the
# matching parser hands each layer's first matched feature to _describe(), which
# projects concrete dates via the shared RecurrenceExpander.
#
# Public holidays shift or cancel collections, and the city publishes them as
# layer 6 with one IMPACT* column per stream. ArcGisHolidayShift loads that layer
# and applies it: the row's waste-type key is mapped back to that layer's
# HOLIDAYFIELD (recorded while describing) by _impact_field(), and the matching
# holiday shifts the date forward/back or cancels the collection.

_LOGGER = logging.getLogger(__name__)

MAPSERVER_BASE = "https://geoweb.shawinigan.ca/arcgis/rest/services/MunicipalServices_DeTravail/MapServer"

HOLIDAYS_LAYER = 6
DEFAULT_HOLIDAY_FIELD = "IMPACTGARB"

# Declarative date parsers: ISO dates in the irregular SCHEDULE list, and the
# JavaScript-style millisecond epoch in the holidays layer's HOLIDAYDATE field.
_iso = date_parsers.for_format("%Y-%m-%d")
_from_ms = date_parsers.from_epoch(unit="ms")

# Each layer: the waste-type string it emits (the legacy t= value, keyed into
# _TYPE_MAP) and the MapServer layer holding it.
LAYERS = [
    ("RECYCLAGE", f"{MAPSERVER_BASE}/0"),  # Blue bin
    ("ORDURES", f"{MAPSERVER_BASE}/1"),  # Grey bin
    ("SAPIN", f"{MAPSERVER_BASE}/2"),  # Christmas tree
    ("FEUILLES", f"{MAPSERVER_BASE}/3"),  # Leaf pickup
    ("COMPOST", f"{MAPSERVER_BASE}/4"),  # Green bin
]

_TYPE_MAP = {
    "RECYCLAGE": wt.RECYCLABLES,
    "ORDURES": wt.GENERAL_WASTE,
    "SAPIN": wt.GARDEN_WASTE,
    "FEUILLES": wt.GARDEN_WASTE,
    "COMPOST": wt.ORGANIC,
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
            d = _iso(part)
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

    The matched feature also carries the layer's HOLIDAYFIELD; that is recorded
    against the waste-type key (each layer's type is distinct) so
    ArcGisHolidayShift can find the matching holiday map for the rows this
    descriptor produces.
    """
    waste_type, attrs = record
    holiday_field = attrs.get("HOLIDAYFIELD") or DEFAULT_HOLIDAY_FIELD

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


def _impact_field(key, source):
    """The holidays layer's IMPACT* column governing this row's collection.

    Each data layer names its own column in the matched feature's HOLIDAYFIELD,
    which _describe() records against the waste-type key (each layer's type is
    distinct). An unrecorded key leaves the row unadjusted.
    """
    if source is None:
        return None
    return source._field_for_key.get(key)


@final
class Source(BaseSource):
    TITLE = "Shawinigan"
    DESCRIPTION = "Source for Shawinigan, Canada waste collection schedule."
    URL = "https://geoweb.shawinigan.ca/CollecteMatieresResiduelles/"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Shawinigan": {"address": "1760 Avenue de la Paix, Shawinigan, QC G9N 6H7"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including city and postal code "
            "(e.g. '1760 Avenue de la Paix, Shawinigan, QC G9N 6H7')."
        ),
    }

    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address="address")
    parse = ArcGisMultiFeatureParser(first_per_layer=True)
    preprocess = Compose(
        RecurrenceExpander(_describe),
        ArcGisHolidayShift(
            f"{MAPSERVER_BASE}/{HOLIDAYS_LAYER}",
            impact_field=_impact_field,
            parse_date=_from_ms,
        ),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
        # Populated in _describe(): {waste_type_key: holiday_field}.
        self._field_for_key: dict[str, str] = {}
