import datetime
from typing import ClassVar, final

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
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
    WasteType,
)

# Demonstrates: the ArcGis service contributing two independent pipeline stages —
# ArcGisFeatureRetriever (raw /query Response) and ArcGisFeatureParser (Response
# -> feature-attribute dicts) — plus the reusable RecurrenceExpander preprocessor.
#
# ArcGIS councils publish one base date per service plus a cadence; the only
# source-specific code is _describe(), which reads those out of the feature. The
# expander fans each Schedule into dates and a plain ICSTransformer types them.

# feature field -> (canonical waste type, cadence). Single source of truth: the
# transformer map is derived from it, and _describe reads the cadence from it.
_SERVICES: dict[str, tuple[WasteType, str]] = {
    "Garbagedate": (GENERAL_WASTE, "weekly"),
    "Recycledate": (RECYCLABLES, "fortnightly"),
    "Fogodate": (ORGANIC, "fortnightly"),
    "Hardwastedate": (BULKY_WASTE, "once"),
}

# cadence -> (step, count) for the recurring projection.
_CADENCE = {
    "weekly": (recurrence.WEEKLY, 26),
    "fortnightly": (recurrence.FORTNIGHTLY, 13),
}


def _describe(attrs, source):
    """Read each service's base date + cadence out of one ArcGIS feature."""
    today = datetime.datetime.now().date()
    service_types = (attrs.get("Servicetypes") or "").upper()
    for field_name, (_waste_type, cadence) in _SERVICES.items():
        # FOGO is only collected where the property is signed up for it.
        if field_name == "Fogodate" and "F" not in service_types:
            continue
        timestamp = attrs.get(field_name)
        if not timestamp:
            continue
        base = datetime.datetime.fromtimestamp(
            timestamp / 1000, tz=datetime.timezone.utc
        ).date()
        if cadence == "once":
            if base >= today:  # one-off (hard waste): only if still upcoming
                yield Schedule(field_name, base)
            continue
        step, count = _CADENCE[cadence]
        yield Schedule(field_name, base, step, count)


@final
class Source(BaseSource):
    TITLE = "Launceston City Council"
    DESCRIPTION = "Source for Launceston City Council waste collection."
    URL = "https://www.launceston.tas.gov.au"
    COUNTRY = "au"

    FEATURE_URL = "https://services.arcgis.com/yeXpdyjk3azbqItW/arcgis/rest/services/Waste/FeatureServer/0"

    TEST_CASES: ClassVar[dict] = {
        "Southgate Dr": {"address": "40 Southgate Dr, Kings Meadows, TAS"},
        "Brisbane St": {"address": "68 Brisbane St, Launceston, TAS"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address, e.g. '40 Southgate Dr, Kings Meadows, TAS'."
        ),
    }

    retrieve = ArcGisFeatureRetriever(FEATURE_URL, address="address")
    parse = ArcGisFeatureParser()
    preprocess = RecurrenceExpander(_describe)

    # Derived from _SERVICES: the rows are tagged with the feature field name.
    transform = ICSTransformer(
        type_value_map={
            field: waste_type for field, (waste_type, _) in _SERVICES.items()
        }
    )

    def __init__(self, address: str):
        super().__init__(address=address)
