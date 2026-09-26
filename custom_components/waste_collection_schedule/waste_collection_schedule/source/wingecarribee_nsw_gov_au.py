import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_ZONE_SERVICE_URL = "https://utility.arcgis.com/usrsvcs/servers/f69ab833f6164175ae4e6e752d109cdb/rest/services/BinDay/BinDayZones1/FeatureServer"

_EPOCH_MS = date_parsers.from_epoch(unit="ms")  # read in UTC

# The collection zones are ten layers of one service; an address lies in one.
_LAYERS = [
    (layer, f"{_ZONE_SERVICE_URL}/{layer}", "Bin,BinDate,BinZoneLabel")
    for layer in range(1, 11)
]


def _describe(record, source):
    """Red bin weekly; yellow (recycling) and green (garden) on alternate weeks.

    ``BinDate`` is a reference collection of the zone (stored as the evening
    before, UTC) and ``Bin`` says which fortnightly bin goes out that week.
    """
    _, attrs = record
    bin_type = attrs.get("Bin")
    if not attrs.get("BinDate") or not bin_type:
        return
    base = _EPOCH_MS(str(attrs["BinDate"])) + datetime.timedelta(days=1)
    other = base + datetime.timedelta(days=7)
    recycling, garden = (base, other) if bin_type == "RedYellow" else (other, base)
    yield Schedule("General Waste", base, recurrence.WEEKLY, 26, anchor=True)
    yield Schedule("Recycling", recycling, recurrence.FORTNIGHTLY, 13, anchor=True)
    yield Schedule("Garden Organics", garden, recurrence.FORTNIGHTLY, 13, anchor=True)


@final
class Source(BaseSource):
    TITLE = "Wingecarribee Shire Council"
    DESCRIPTION = "Source for Wingecarribee Shire Council (NSW) waste collection."
    URL = "https://www.wsc.nsw.gov.au"
    COUNTRY = "au"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@m1ckyb"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Willow Road": {"address": "8 Willow Road, Bowral NSW 2576"},
        "Badgery Street": {"address": "12 Badgery Street, Willow Vale NSW 2575"},
        "Willow Drive": {"address": "56 Willow Drive, Moss Vale NSW 2577"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter the full street address including suburb, state and postcode.",
    }

    # The service sits behind an ArcGIS Online proxy that only answers the
    # council's web map.
    retrieve = ArcGisMultiFeatureRetriever(
        _LAYERS,
        first_match=True,
        argument="address",
        headers={
            "Referer": "https://wscweb.maps.arcgis.com/",
            "Origin": "https://wscweb.maps.arcgis.com",
        },
    )
    parse = ArcGisMultiFeatureParser(first_per_layer=True)
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Organics": wt.GARDEN_WASTE,
        }
    )
