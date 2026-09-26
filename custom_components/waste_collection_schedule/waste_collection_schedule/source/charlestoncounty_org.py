import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_FEATURE_URL = "https://services.arcgis.com/jR9eNCjAkxwH2nLe/arcgis/rest/services/Curbside_Recycling_Days/FeatureServer/0"

# The county publishes only the next pickup, without a year ("October 02");
# recycling then recurs every two weeks.
_PICKUPS_AHEAD = 13


def _describe(record, source):
    value = (record.get("PickupDate") or "").strip()
    if not value:
        return
    try:
        parsed = datetime.datetime.strptime(value, "%B %d").date()
    except ValueError:
        return
    today = datetime.date.today()
    pickup = parsed.replace(year=today.year)
    # A January pickup published in December belongs to the next year.
    if (today - pickup).days > 30:
        pickup = pickup.replace(year=today.year + 1)
    # A layer briefly stale after a pickup keeps its fortnightly cadence.
    yield Schedule(
        "Recycling", pickup, recurrence.FORTNIGHTLY, _PICKUPS_AHEAD, anchor=True
    )


@final
class Source(BaseSource):
    TITLE = "Charleston County, SC"
    DESCRIPTION = "Source for Charleston County, SC residential curbside recycling."
    URL = "https://www.charlestoncounty.org/departments/environmental-management/recycle.php"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@dmkjr"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Downtown Charleston": {"address": "123 Coming St, Charleston, SC 29403"},
        "Johns Island": {"address": "2758 August Rd, Johns Island, SC 29455"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter the full street address including city, state, and ZIP code.",
    }

    retrieve = ArcGisFeatureRetriever(_FEATURE_URL, out_fields="PickupDate")
    parse = ArcGisFeatureParser(argument="address")
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map={"Recycling": wt.RECYCLABLES})
