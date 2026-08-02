from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    Schedule,
    SelectExactMatch,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Selwyn's ArcGIS layer is queried with an address-prefix `where` clause, so a
# short fragment can come back holding several distinct properties' rows.
# ``SelectExactMatch`` keeps the rows of the one property the address names (and
# asks the user to disambiguate when it names none of them), each remaining row
# describes its own round's weekday and cadence, and ``Deduplicate`` collapses
# the several red-bin charges a property is billed for into one rubbish round.

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


def _describe(attrs: dict, source):
    """One charge row -> its round's weekday and cadence."""
    # Bound the projection to the same fixed [today, today + WEEKS_AHEAD*7)
    # window the legacy day-by-day loop used, rather than a fixed occurrence
    # count, so a fortnightly recycling cadence and the weekly streams cover
    # exactly the same span.
    window_end = date.today() + timedelta(days=WEEKS_AHEAD * 7 - 1)
    weekday = recurrence.weekday(attrs.get("COLLECTION_DAY") or "")
    if weekday is None:
        return
    label = _label_for_charge(attrs.get("ChargeType", ""))
    start = recurrence.next_weekday(weekday)
    if label == RECYCLING:
        # Only the recycling row carries a meaningful schedule ("1"/"2"): which
        # half of the council's two-weekly cycle this property is collected in.
        schedule = (attrs.get("COLLECTION_SCHEDULE") or "").strip()
        if schedule not in ("1", "2"):
            return
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
    parse = ArcGisFeatureParser(argument="address")
    preprocess = Compose(
        SelectExactMatch(
            argument="address", key=lambda attrs: attrs.get("Address_full")
        ),
        RecurrenceExpander(_describe),
        Deduplicate(),
    )
    transform = RowTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
