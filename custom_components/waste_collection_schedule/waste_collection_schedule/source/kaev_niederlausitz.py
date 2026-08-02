"""KAEV Niederlausitz (kaev.de).

Demonstrates: the "warm up the session, POST a JSON lookup, GET the calendar it
names" shape, which is ``IcsSessionRetriever`` with two steps. The lookup's
``extract`` mirrors the legacy source's match-count branching (one match -> use
it; several matches but no district given -> default to the first Ort-level
match; otherwise ambiguous/not found) and hands the resolved calendar URL
forward as the feed URL.

The feed is a rolling window rather than a per-year calendar, hence
``lookahead_month=None``: running the chain a second time in December would
only duplicate every entry.

Two provider quirks the legacy source patched by hand are now shared repairs in
``service/ICS.py``, because neither is specific to this provider: the empty
``BEGIN:VTIMEZONE`` / ``TZID:W. Europe Standard Time`` / ``END:VTIMEZONE``
shell (dropped along with the ``TZID=`` parameters naming it) and the trailing
``", "`` some summaries carry, which ``ICSTransformer(clean=...)`` strips
before the label is resolved.
"""

import html
import json
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, PAPER

HOME_URL = "https://www.kaev.de/"
LOOKUP_URL = (
    "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/ajax.aspx/getAddress"
)
CALENDAR_URL = "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/iCal.aspx"


def _lookup_body(abf_suche: str, **_) -> "dict[str, str]":
    return {"query": abf_suche}


def _calendar_url(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """Resolve the search term to the one calendar it names."""
    query = context["abf_suche"]
    matches = json.loads(response.json()["d"])

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

    return {"calendar_url": calendar_url}


@final
class Source(BaseSource):
    TITLE = "KAEV Niederlausitz"
    DESCRIPTION = "Source for Kommunaler Abfallverband Niederlausitz waste collection."
    URL = "https://www.kaev.de/"
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Luckau / OT Zieckau": {"abf_suche": "Luckau / OT Zieckau"},
        "Luckau Bersteweg": {"abf_suche": "Luckau / Bersteweg"},
        "Staakow": {"abf_suche": "Staakow"},
    }

    PARAMS = (text_field("abf_suche", label="Search term"),)
    RAISE_ON_EMPTY = True

    retrieve = IcsSessionRetriever(
        steps=[
            # The site hands out its session cookie on the homepage; the lookup
            # only answers once that has been collected.
            {"url": HOME_URL},
            {
                "method": "POST",
                "url": LOOKUP_URL,
                "json": _lookup_body,
                "extract": _calendar_url,
            },
        ],
        feed_url=lambda calendar_url, **_: calendar_url,
        encoding="utf-8",
        lookahead_month=None,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(clean=lambda title: title.removesuffix(", "))

    def __init__(self, abf_suche: str):
        super().__init__(abf_suche=abf_suche)
