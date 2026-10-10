"""City of Wodonga, Victoria (Australia).

The council's "Albury-Wodonga Waste Collection" lookup is an ArcGIS app over a
public FeatureServer layer of collection-day polygons ("Collection Monday" ...
"Collection Friday"). The address is geocoded with the Esri World geocoder and
the polygon it falls in gives the collection weekday.

Rotation: Organics (green lid, FOGO) is collected every week on that day;
Recycling (yellow lid) and General Waste (red lid) alternate fortnightly on the
same day. The layer carries no week A/B field, but the council publishes one
city-wide calendar (HalveWaste "2026 Collection Calendar - Wodonga", linked
from the council's Bins and Collection page) that colours every week: the week
starting Monday 2 February 2026 is a Recycling week, and the colours strictly
alternate through all of 2026, including public holidays (Christmas Day and
Good Friday are collected as normal). Recycling and General Waste are therefore
anchored fortnights from that Monday plus the weekday offset, which keeps
alternating across year ends (2026 has an ISO week 53, so ISO-week parity would
break on 2027-01-04). The 2027 calendar was not yet published when this was
written; if it restarts the pattern, move the anchor.
"""

import datetime
from collections.abc import Iterator
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    RequireRecords,
    Schedule,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisFeatureParser,
    ArcGisFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_FEATURE_URL = (
    "https://services-ap1.arcgis.com/w6r4LlwgJu8O0neQ/arcgis/rest/services"
    "/waste_collection_view/FeatureServer/0"
)
_WEEKS_AHEAD = 26

# Monday starting a Recycling week on the council's 2026 collection calendar.
_RECYCLING_WEEK_MONDAY = datetime.date(2026, 2, 2)

_TYPE_MAP = {
    "Organics": wt.ORGANIC,
    "Recycling": wt.RECYCLABLES,
    "General Waste": wt.GENERAL_WASTE,
}


def _geocode_address(address: str) -> str:
    """Qualify the address so the world geocoder resolves it in Victoria."""
    return f"{address}, Victoria, Australia"


def _describe(record: dict[str, Any], source: Any) -> Iterator[Schedule]:
    # "Collection Monday" -> "Monday"
    day = (record.get("type") or "").replace("Collection", "").strip()
    weekday = recurrence.weekday(day)
    if weekday is None:
        return
    yield Schedule(
        "Organics", recurrence.next_weekday(weekday), recurrence.WEEKLY, _WEEKS_AHEAD
    )
    recycling = _RECYCLING_WEEK_MONDAY + datetime.timedelta(days=weekday)
    yield Schedule(
        "Recycling", recycling, recurrence.FORTNIGHTLY, _WEEKS_AHEAD // 2, anchor=True
    )
    yield Schedule(
        "General Waste",
        recycling + datetime.timedelta(weeks=1),
        recurrence.FORTNIGHTLY,
        _WEEKS_AHEAD // 2,
        anchor=True,
    )


@final
class Source(BaseSource):
    TITLE = "City of Wodonga"
    DESCRIPTION = "Source for City of Wodonga (Victoria) kerbside collection."
    URL = "https://www.wodonga.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.ORGANIC, wt.RECYCLABLES, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Wodonga Council offices - Monday": {"address": "104 Hovell St, Wodonga"},
        "Baranduda Fields - Wednesday": {"address": "160 Kiewa Valley Hwy, Baranduda"},
        "Wodonga TAFE - Friday": {"address": "87 McKoy St, West Wodonga"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Outside Wodonga": {"address": "1 Swanston St, Melbourne"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address in the City of Wodonga, e.g. "
            "'104 Hovell St, Wodonga'. Organics is collected weekly; Recycling "
            "and General Waste alternate fortnightly on the same day, as on "
            "the council's collection calendar at "
            "https://www.wodonga.vic.gov.au/Services/Recycling-and-Waste/Bins-and-Collection."
        ),
    }

    retrieve = ArcGisFeatureRetriever(
        _FEATURE_URL, address=_geocode_address, out_fields="type"
    )
    parse = ArcGisFeatureParser()
    preprocess = Compose(
        RequireRecords(
            argument="address",
            hint="The address is not inside the City of Wodonga collection area.",
        ),
        RecurrenceExpander(_describe),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
