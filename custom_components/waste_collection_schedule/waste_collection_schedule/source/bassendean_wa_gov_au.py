import datetime

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

# ArcGis single spatial query -> one feature carrying a ServiceDay, from which
# three recurring schedules are projected: FOGO weekly, and General Waste and
# Recycling fortnightly on opposite weeks. Acquisition + parse are the shared
# ArcGis components; the only source-specific code is _describe (the council's
# per-weekday base dates and anchoring logic).

FEATURE_URL = "https://services-ap1.arcgis.com/551UnqKK1GZeDKxQ/arcgis/rest/services/address_lookup_for_bin_days_dissolved/FeatureServer/0"

_TYPE_MAP = {
    "FOGO": ORGANIC,
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
}

# Base dates for fortnightly schedules, extracted from the ArcGIS Arcade
# expressions in the web map config. General Waste and Recycling alternate
# on opposite fortnights.
_GENERAL_WASTE_BASE: dict[str, datetime.date] = {
    "Monday": datetime.date(2025, 3, 31),
    "Tuesday": datetime.date(2025, 4, 1),
    "Wednesday": datetime.date(2025, 4, 2),
    "Thursday": datetime.date(2025, 4, 3),
    "Friday": datetime.date(2025, 4, 4),
}

_RECYCLING_BASE: dict[str, datetime.date] = {
    "Monday": datetime.date(2025, 3, 24),
    "Tuesday": datetime.date(2025, 3, 25),
    "Wednesday": datetime.date(2025, 3, 26),
    "Thursday": datetime.date(2025, 3, 27),
    "Friday": datetime.date(2025, 3, 28),
}


def _describe(attrs, source):
    day = (attrs.get("ServiceDay") or "").strip()
    weekday = recurrence.weekday(day)
    if weekday is None:
        return

    # FOGO — weekly.
    yield Schedule("FOGO", recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)

    # General Waste — fortnightly, pinned to a historical base date.
    general_base = _GENERAL_WASTE_BASE.get(day)
    if general_base is not None:
        yield Schedule(
            "General Waste", general_base, recurrence.FORTNIGHTLY, 13, anchor=True
        )

    # Recycling — fortnightly, on the opposite week.
    recycling_base = _RECYCLING_BASE.get(day)
    if recycling_base is not None:
        yield Schedule(
            "Recycling", recycling_base, recurrence.FORTNIGHTLY, 13, anchor=True
        )


class Source(BaseSource):
    TITLE = "Town of Bassendean"
    DESCRIPTION = "Source for Town of Bassendean waste collection."
    URL = "https://www.bassendean.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Kenny St": {"address": "16 Kenny St, Bassendean"},
        "Broadway": {"address": "50 Broadway, Bassendean"},
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address within the Town of Bassendean "
            "(e.g. '16 Kenny St, Bassendean')."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        FEATURE_URL, address="address", out_fields="ServiceDay"
    )
    parse = ArcGisFeatureParser()
    preprocessor = RecurrenceExpander(_describe)

    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
