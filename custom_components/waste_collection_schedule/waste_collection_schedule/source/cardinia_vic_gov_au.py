import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_ZONES_URL = "https://services3.arcgis.com/TJxZpUnYIJOvcYwE/arcgis/rest/services/Waste_Collection_Zones/FeatureServer/0"

# Each zone gives, per bin, a first collection date and a rhythm in weeks
# ("rub_start": "2017-07-31", "rub_weeks": 1). The next four weeks are listed.
_BINS = {"rub": "Rubbish", "rec": "Recycling", "grn": "Green Waste"}
_WEEKS_AHEAD = 4


def _describe(record, source):
    for prefix, key in _BINS.items():
        start = record.get(f"{prefix}_start")
        weeks = record.get(f"{prefix}_weeks")
        if not start or not weeks:
            continue
        yield Schedule(
            key,
            datetime.date.fromisoformat(start),
            datetime.timedelta(weeks=int(weeks)),
            _WEEKS_AHEAD // int(weeks),
            anchor=True,
        )


@final
class Source(BaseSource):
    TITLE = "Cardinia Shire Council"
    DESCRIPTION = "Source script for cardinia.vic.gov.au"
    URL = "https://www.cardinia.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "1015 Manks Rd": {"address": "1015 Manks Rd, Dalmore Vic"},  # Monday
        "6-8 Main St": {"address": "6-8 Main St, Nar Nar Goon Vic"},  # Tuesday
        "875 Princes Hwy": {"address": "875 Princes Hwy, Pakenham Vic"},  # Thursday
        "124 Main St": {"address": "124 Main St, Pakenham Vic"},  # Friday
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address including suburb (e.g. '124 Main St, Pakenham Vic').",
    }

    retrieve = ArcGisFeatureRetriever(_ZONES_URL, result_record_count=1)
    parse = ArcGisFeatureParser(argument="address")
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green Waste": wt.GARDEN_WASTE,
        }
    )
