"""Kumberg (kumberg.gv.at).

Not a TwoStepRetriever shape: there is no user-supplied lookup key at all. The
calendar index page lists a fixed, small set of per-waste-type ICS feed URLs
(one per ``i.fa-calendar-plus`` icon whose link contains "abfalltyp"), and every
feed is fetched and combined. ``service.ICS.IcsIndexRetriever`` covers that
shape; the events page on the same site publishes its own ``?ical=download``
links, which is why the href pattern narrows the selection to the waste ones.

Two of the bins carry their drop-off window in the feed's SUMMARY ("Sperrmüll
7.00 - 9.30 Uhr"); ``parsers.IcsParser``'s ``regex`` option trims it back to the
bin name so the shared vocabulary can resolve it.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsIndexRetriever
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://www.kumberg.gv.at/kalender/"

# Trims a time-range suffix like "7.00 - 9.30 Uhr" off a bin type label.
_TIME_RANGE = r"(.*?)\s*\d{1,2}\.\d{2} - \d{1,2}\.\d{2} Uhr"


@final
class Source(BaseSource):
    TITLE = "Kumberg"
    DESCRIPTION = "Source for Kumberg."
    URL = "https://www.kumberg.gv.at"
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {"Whole Kumberg": {}}

    retrieve = IcsIndexRetriever(
        index_url=API_URL,
        link_selector="i.fa-calendar-plus",
        pattern=r"abfalltyp",
    )

    parse = IcsFeedsParser(parsers.IcsParser(regex=_TIME_RANGE))

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Bio": wt.ORGANIC,
            "Papier": wt.PAPER,
            "Gelber Sack": wt.RECYCLABLES,
            "Sperrmüll": wt.BULKY_WASTE,
        },
    )
