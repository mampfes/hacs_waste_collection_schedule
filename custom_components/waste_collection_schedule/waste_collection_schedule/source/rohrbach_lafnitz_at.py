from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.RiSKommunalAT import ICS_AQN, ICS_PATH
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import BULKY_WASTE, GARDEN_WASTE

# Demonstrates: a RiSKommunal municipality that publishes one ICS feed *per
# waste type* rather than one combined calendar. Each feed's own ICS SUMMARY is
# generic/unhelpful, so the legacy source tagged every event with the dict key
# under which its "do" id was listed (RiSKommunalSource.fetch_ics_by_label),
# not the feed's own SUMMARY text. There is no dedicated multi-feed retriever
# in the pipeline yet, so this is expressed with a source-defined
# retrieve()/parse() pair: fetch each labelled feed via source.session, then
# reuse the shared parsers.IcsParser() per feed and re-tag every event with its
# calendar's label.

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


def _ics_url(do: str) -> str:
    return f"{_BASE_URL}{ICS_PATH}?aqn={ICS_AQN}&sprache=1&gnr={_GNR}&do={do}"


@final
class Source(BaseSource):
    TITLE = "Rohrbach an der Lafnitz"
    DESCRIPTION = "Source for Rohrbach an der Lafnitz, Austria."
    URL = _BASE_URL
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {
        "All waste types": {},
    }

    PARAMS = ()

    # Biomüll, Leichtverpackungen and Restmüll are classified by the shared
    # vocabulary; only the combined bulky-waste/hedge-trimmings round needs an
    # explicit entry.
    transform = ICSTransformer(
        type_value_map={
            "Sperrmüll & Heckenschnitt": [BULKY_WASTE, GARDEN_WASTE],
        },
    )

    def retrieve(self, source):
        # One ICS feed per waste type; fetch every feed via the shared session
        # and keep each response paired with the label its "do" id stands for.
        return [
            (label, source.session.get(_ics_url(do), timeout=30))
            for label, do in _ICS_CALENDARS.items()
        ]

    def parse(self, raw, source):
        # Reuse the shared IcsParser per feed (rather than hand-rolling ICS
        # parsing), discarding its SUMMARY in favour of the feed's own label.
        ics_parser = IcsParser()
        for label, response in raw:
            for event_date, _summary in ics_parser(response, source):
                yield event_date, label
