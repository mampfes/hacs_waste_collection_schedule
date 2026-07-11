"""Kumberg (kumberg.gv.at).

Not a TwoStepRetriever shape: there is no user-supplied lookup key at all. The
calendar index page lists a fixed, small set of per-waste-type ICS feed URLs
(one per ``i.fa-calendar-plus`` icon whose link contains "abfalltyp"); every
feed is fetched and combined. A source-defined ``retrieve``/``parse`` pair
covers this (no shared retriever fits "scrape an index page for N feed URLs,
fetch every one").
"""

import re
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

API_URL = "https://www.kumberg.gv.at/kalender/"

# Strips a time-range suffix like "7.00 - 9.30 Uhr" from a bin type label.
_TIME_RANGE = re.compile(r"\d{1,2}\.\d{2} - \d{1,2}\.\d{2} Uhr")


@final
class Source(BaseSource):
    TITLE = "Kumberg"
    DESCRIPTION = "Source for Kumberg."
    URL = "https://www.kumberg.gv.at"
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {"Whole Kumberg": {}}

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Bio": ORGANIC,
            "Papier": PAPER,
            "Gelber Sack": RECYCLABLES,
            "Sperrmüll": BULKY_WASTE,
        },
    )

    def retrieve(self, source):
        index = source.session.get(API_URL)
        soup = BeautifulSoup(index.text, "html.parser")
        urls: set[str] = set()
        for icon in soup.select("i.fa-calendar-plus"):
            parent = icon.parent
            href = parent.get("href") if isinstance(parent, Tag) else None
            if isinstance(href, str) and "abfalltyp" in href:
                urls.add(href)
        return [source.session.get(url) for url in urls]

    def parse(self, responses, source=None):
        ics = ICS()
        events: list[tuple] = []
        for response in responses:
            for date_, bin_type in ics.convert(response.text):
                events.append((date_, _TIME_RANGE.sub("", bin_type).strip()))
        return events

    def __init__(self):
        super().__init__()
