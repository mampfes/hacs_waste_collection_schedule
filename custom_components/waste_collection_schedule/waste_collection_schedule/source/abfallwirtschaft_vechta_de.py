"""AWB Abfallwirtschaft Vechta, Germany.

Demonstrates: a per-street calendar assembled from *two* independent paper-
collector feeds ("pamo" and "siemer"), each needing the same chain of id
lookups (city search, then street search, threading the previous answer
through the query and a growing cookie jar) before its own ICS download. That
is ``IcsSessionRetriever`` with two steps and two ``variants``; near year-end
the provider also publishes the first weeks of the following year, which the
retriever's lookahead picks up best-effort. The two feeds repeat every shared
collection, so the labels are tidied and de-duplicated in ``IcsFeedsParser``
before the records reach ``ICSTransformer``: a stripped per-district digit
does not change the record's canonical waste type, only its now-superseded
display text.
"""

import json
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.abfallwirtschaft-vechta.de"
_STADT_SUCHE_URL = f"{_BASE_URL}/CALENDER/inc.suche_stadt.php"
_STRASSE_SUCHE_URL = f"{_BASE_URL}/CALENDER/inc.suche_strasse.php"
_ICS_URL = f"{_BASE_URL}/CALENDER/inc.get_calender_ics.php"

_TITLE_STRIP = ("Abfuhrtermin", "Erinnerung", "für")
_DIGITS_RE = re.compile(r"[0-9]")


def _clean_bin_type(title: str) -> str:
    """Strip the fixed wording and the per-district digit off a summary."""
    for phrase in _TITLE_STRIP:
        title = title.replace(phrase, "")
    title = _DIGITS_RE.sub("", title).strip().replace("  ", " ")
    return title


def _street_entry(response, context) -> dict:
    """Read the street's ids out of the search response's padded JSON."""
    entry = json.loads(response.text[1:-2])["strassen"][0]
    return {
        "strasse_id": entry["id"],
        "abfuhrbezirk": entry["abfuhrbezirk"],
        # Each paper contractor runs its own district numbering.
        "abfuhrbezirkpapier": entry[context["variant"]],
    }


def _street_cookies(strasse_id, abfuhrbezirk, abfuhrbezirkpapier, variant, **_) -> dict:
    """What the site puts in the jar once a street is chosen.

    The paper district's cookie name is spelt without the "e"
    ("abfuhrbezirkpapir"), unlike the query argument; the server reads both.
    """
    return {
        "stadt": str(strasse_id),
        "abfuhrbezirk": str(abfuhrbezirk),
        "abfuhrbezirkpapir": str(abfuhrbezirkpapier),
        "papier": variant,
    }


def _feed_params(stadt_id, strasse_id, abfuhrbezirkpapier, year, variant, **_) -> dict:
    return {
        "stadt": stadt_id,
        "strasse": strasse_id,
        "abfuhrbezirkpapier": abfuhrbezirkpapier,
        "jahr": year,
        "papier": variant,
        "trigger": "false",
        "triggerday": "false",
        "triggertime": "false",
    }


@final
class Source(BaseSource):
    TITLE = "AWB Abfallwirtschaft Vechta"
    DESCRIPTION = "Source for AWB Abfallwirtschaft Vechta."
    URL = f"{_BASE_URL}/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Vechta, An der Hasenweide": {
            "stadt": "Vechta",
            "strasse": "An der Hasenweide",
        },
        "Bakum, Up'n Sande": {"stadt": "Bakum", "strasse": "Up'n Sande"},
        "Neuenkirchen-Vörden, Braunschweiger Straße": {
            "stadt": "Neuenkirchen-Vörden",
            "strasse": "Braunschweiger Straße",
        },
        "Goldenstedt, An der Ellenbäke": {
            "stadt": "Goldenstedt",
            "strasse": "An der Ellenbäke",
        },
    }

    PARAMS = (
        city(field="stadt"),
        street(field="strasse"),
    )

    retrieve = IcsSessionRetriever(
        variants=("pamo", "siemer"),
        cookies=lambda year, **_: {"jahr": str(year)},
        steps=[
            {
                "url": _STADT_SUCHE_URL,
                "params": lambda stadt, **_: {"term": stadt},
                "extract": lambda response, _: {"stadt_id": response.json()[0]["id"]},
                "cookies": lambda stadt_id, **_: {"stadt": str(stadt_id)},
            },
            {
                "url": _STRASSE_SUCHE_URL,
                "params": lambda stadt_id, strasse, **_: {
                    "stadt": stadt_id,
                    "term": strasse,
                },
                "extract": _street_entry,
                "cookies": _street_cookies,
            },
        ],
        feed_url=_ICS_URL,
        feed_params=_feed_params,
        encoding="utf-8",
    )

    parse = IcsFeedsParser(parsers.IcsParser(), clean=_clean_bin_type, dedupe=True)

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": GENERAL_WASTE,
            "Glass": GLASS,
            "Glas": GLASS,
            "Bioabfall": ORGANIC,
            "Altpapier": PAPER,
            "Altpapier Siemer": PAPER,
            "Altpapier Pamo": PAPER,
            "Gelbe Tonne": RECYCLABLES,
            "Altkleider": RECYCLABLES,
            "Altkleider (Außer Langförden)": RECYCLABLES,
            "Mobile Schadstoff.": HAZARDOUS,
        }
    )

    def __init__(self, stadt: str, strasse: str):
        super().__init__(stadt=stadt, strasse=strasse)
