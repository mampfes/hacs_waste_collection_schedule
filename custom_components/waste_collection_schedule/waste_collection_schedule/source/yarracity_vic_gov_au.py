import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# City of Yarra publishes its collection zones on one MapServer with two
# layers: layer 1 (waste) carries the property's collection weekday and the
# anchor date that fixes its fortnightly recycling phase, layer 0 (glass)
# carries an independent anchor plus the glass cycle length in days. Both are
# point-in-polygon lookups from a single geocode, which is exactly what the
# shared multi-layer ArcGIS retriever does, so the only source-specific code
# is _describe() (reading those fields) and _adjust() (the council's own
# public-holiday rule).

MAP_SERVER_URL = (
    "https://yccgis-prd.esriaustraliaonline.com.au/arcgis/rest/services/"
    "Waste_Services/CW_FC_PRD_Waste_Collection/MapServer"
)

GLASS_LAYER = "glass"
WASTE_LAYER = "waste"

# (label, feature_url, out_fields) per layer; the label is carried through to
# each parsed record so _describe() knows which fields it is looking at.
LAYERS = [
    (GLASS_LAYER, f"{MAP_SERVER_URL}/0", "anchor_date,frequency_days"),
    (WASTE_LAYER, f"{MAP_SERVER_URL}/1", "collection_day,recycling_anchor_date"),
]

# How many weekly collections to project; the fortnightly and glass cycles
# cover the same horizon at their own cadence.
WEEKS_AHEAD = 52

_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Glass": wt.GLASS,
    "FOGO": wt.ORGANIC,
}


def _geocode_address(address: str) -> str:
    """Qualify the address so the world geocoder resolves it in Victoria."""
    return f"{address}, Victoria, Australia"


def _to_date(value: object) -> datetime.date | None:
    """Read an ArcGIS date field, which these layers publish as an ISO string."""
    if isinstance(value, str) and value:
        return datetime.date.fromisoformat(value[:10])
    if isinstance(value, (int, float)):
        return datetime.date.fromtimestamp(value / 1000)
    return None


def _describe(record, source):
    """Project a layer's matched feature into its Schedule descriptors.

    ``record`` is the ``(label, attrs)`` pair produced by
    :class:`ArcGisMultiFeatureParser`. Every schedule is anchored, so its
    historical start date is rolled forward to the first occurrence on or
    after today before the dates are generated.
    """
    label, attrs = record

    if label == WASTE_LAYER:
        weekday = recurrence.weekday(attrs.get("collection_day") or "")
        if weekday is not None:
            # Rubbish and FOGO both run weekly on the property's collection
            # day, today's collection included when that day is today.
            start = recurrence.most_recent_weekday(weekday)
            yield Schedule(
                "Rubbish", start, recurrence.WEEKLY, WEEKS_AHEAD, anchor=True
            )
            yield Schedule("FOGO", start, recurrence.WEEKLY, WEEKS_AHEAD, anchor=True)

        # Recycling alternates fortnightly between zones; the layer's anchor
        # date fixes this property's phase.
        recycling_anchor = _to_date(attrs.get("recycling_anchor_date"))
        if recycling_anchor is not None:
            yield Schedule(
                "Recycling",
                recycling_anchor,
                recurrence.FORTNIGHTLY,
                WEEKS_AHEAD // 2,
                anchor=True,
            )
        return

    # Glass runs on its own cycle (currently every 28 days) with an
    # independent per-polygon anchor and cycle length.
    glass_anchor = _to_date(attrs.get("anchor_date"))
    frequency = attrs.get("frequency_days")
    if glass_anchor is not None and frequency:
        yield Schedule(
            "Glass",
            glass_anchor,
            datetime.timedelta(days=int(frequency)),
            WEEKS_AHEAD // 4,
            anchor=True,
        )


def _adjust(collection_date: datetime.date, key: str, source) -> datetime.date:
    """Council rule: collections run on every public holiday except Good
    Friday and Christmas Day, when they happen one day later."""
    if collection_date == recurrence.good_friday(collection_date.year) or (
        collection_date.month == 12 and collection_date.day == 25
    ):
        return collection_date + datetime.timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "City of Yarra"
    DESCRIPTION = "Source for City of Yarra waste collection."
    URL = "https://www.yarracity.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@yeaaaaaahh"]

    TEST_CASES: ClassVar[dict] = {
        "Fitzroy Town Hall": {"address": "201 Napier Street, Fitzroy VIC 3065"},
        "Richmond Town Hall": {"address": "333 Bridge Road, Richmond VIC 3121"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your full street address including suburb and postcode, "
            "e.g. '333 Bridge Road, Richmond VIC 3121'."
        ),
    }

    # Declarative pipeline: geocode once, spatially query both layers, tag each
    # response with its label, then project each match into concrete dates and
    # defer the two days the council does not collect on.
    retrieve = ArcGisMultiFeatureRetriever(LAYERS, address=_geocode_address)
    parse = ArcGisMultiFeatureParser()
    preprocess = Compose(RecurrenceExpander(_describe), HolidayShift(_adjust))
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
