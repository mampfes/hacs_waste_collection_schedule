"""KAEV Niederlausitz (kaev.de).

Not a TwoStepRetriever shape: the lookup is a POST with a JSON body (preceded
by a plain GET to the homepage that seeds the session), not a GET, so
``TwoStepRetriever`` (which only issues GETs) doesn't fit. A source-defined
``retrieve`` covers the warm-up GET, the POST lookup and the final ICS GET,
and mirrors the legacy source's exact match-count branching (one match ->
use it; several matches but no district given -> default to the first
Ort-level match; otherwise ambiguous/not found).
"""

import html
import json
import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer

LOOKUP_URL = (
    "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/ajax.aspx/getAddress"
)
CALENDAR_URL = "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/iCal.aspx"

# A malformed VTIMEZONE block some feeds embed, which trips up the ICS parser.
_BROKEN_VTIMEZONE = re.compile(r"BEGIN:VTIMEZONE.*?END:VTIMEZONE\r?\n", re.DOTALL)


@final
class Source(BaseSource):
    TITLE = "KAEV Niederlausitz"
    DESCRIPTION = "Source for Kommunaler Abfallverband Niederlausitz waste collection."
    URL = "https://www.kaev.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Luckau / OT Zieckau": {"abf_suche": "Luckau / OT Zieckau"},
        "Luckau Bersteweg": {"abf_suche": "Luckau / Bersteweg"},
        "Staakow": {"abf_suche": "Staakow"},
    }

    PARAMS = (text_field("abf_suche", label="Search term"),)
    RAISE_ON_EMPTY = True

    transform = ICSTransformer()

    def retrieve(self, source):
        query = source.params["abf_suche"]

        source.session.get("https://www.kaev.de/")
        lookup = source.session.post(LOOKUP_URL, json={"query": query})
        matches = json.loads(lookup.json()["d"])

        calendar_url = ""
        if len(matches) == 1:
            entry = matches[0]
            calendar_url = html.escape(
                f"{CALENDAR_URL}?Ort={entry['name']}"
                f"&OrtId={entry['ortId']}&OrtsteilId={entry['ortsteilId']}"
            )
        elif "/" not in query:
            # No district specified: default to the first Ort-level match.
            matches = matches[:1]
            if matches:
                entry = matches[0]
                calendar_url = html.escape(
                    f"{CALENDAR_URL}?Ort={entry['name']}&OrtId={entry['ortId']}"
                )

        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "abf_suche", query, [entry["name"] for entry in matches]
            )
        if len(matches) == 0:
            raise SourceArgumentNotFound("abf_suche", query)

        return source.session.get(calendar_url)

    def parse(self, response, source=None):
        response.encoding = "utf-8"
        ics_text = response.text
        if (
            "BEGIN:VTIMEZONE\r\nTZID:W. Europe Standard Time\r\nEND:VTIMEZONE"
            in ics_text
        ):
            ics_text = _BROKEN_VTIMEZONE.sub("", ics_text)
            ics_text = ics_text.replace("TZID=W. Europe Standard Time;", "")
        return [
            (date_, label.removesuffix(", "))
            for date_, label in ICS().convert(ics_text)
        ]

    def __init__(self, abf_suche: str):
        super().__init__(abf_suche=abf_suche)
