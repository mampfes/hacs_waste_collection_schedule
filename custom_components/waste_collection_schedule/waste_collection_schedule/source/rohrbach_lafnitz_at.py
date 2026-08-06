from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalMultiIcsParser,
    RiSKommunalMultiIcsRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a RiSKommunal municipality that publishes one ICS feed *per
# waste type* rather than one combined calendar. Each feed's own ICS SUMMARY is
# generic/unhelpful, so every feed is re-tagged with the label its "do" id is
# listed under (RiSKommunalMultiIcsRetriever's ``feeds`` mapping), not the
# feed's own SUMMARY text.

_BASE_URL = "https://www.rohrbach-lafnitz.at"
_GNR = "2371"

# Calendar "do" ids, keyed by the waste-type label to tag their events with
# (the label the legacy source used, not the feed's own SUMMARY).
_ICS_CALENDARS: dict[str, str] = {
    "Biomüll": "MjI1MTc2NDk0",
    "Leichtverpackungen": "MjI1MTc2NDg4",
    "Restmüll": "MjI1MTc2NDky",
    "Sperrmüll & Heckenschnitt": "MjI1MTc2NDk2",
}


@final
class Source(BaseSource):
    TITLE = "Rohrbach an der Lafnitz"
    DESCRIPTION = "Source for Rohrbach an der Lafnitz, Austria."
    URL = _BASE_URL
    COUNTRY = "at"

    # The vocabulary this feed actually produces, derived by replaying the
    # recorded cassette. Declared explicitly because most of these labels are
    # resolved by the shared vocabulary rather than listed in type_value_map,
    # so the auto-derived set would be incomplete.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "All waste types": {},
    }

    PARAMS = ()

    retrieve = RiSKommunalMultiIcsRetriever(
        base_url=_BASE_URL, gnr=_GNR, feeds=_ICS_CALENDARS
    )
    parse = RiSKommunalMultiIcsParser()

    # Biomüll, Leichtverpackungen and Restmüll are classified by the shared
    # vocabulary; only the combined bulky-waste/hedge-trimmings round needs an
    # explicit entry.
    transform = ICSTransformer(
        type_value_map={
            "Sperrmüll & Heckenschnitt": [wt.BULKY_WASTE, wt.GARDEN_WASTE],
        },
    )
