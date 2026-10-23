"""SICTOM du Val de Saône, Haute-Saône, France.

The SICTOM's website shows a clickable image map whose areas (one per commune)
link to a PDF leaflet. The map's data sits in a JavaScript file
(``image-map-pro.min.js``): ``map_commune`` reads each area's title and link
from it. The leaflet states the rounds as text ("COLLECTES DU TRI TOUS LES
JEUDIS SEMAINES PAIRES"), a weekday and an ISO-week parity, which
``leaflet_schedules`` turns into recurring schedules; ``RecurrenceExpander``
projects them and the three public holidays that defer a round by one day are
shifted.
"""

import datetime
import difflib
import json
import re
import unicodedata
from typing import Any, ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_JS_URL = "https://www.sictomvds.com/map/image-map-pro.min.js"

_GENERAL = "Ordures ménagères"
_RECYCLING = "Tri"

# Only these three public holidays defer a round by one day; the others are
# worked normally.
_DEFERRED_HOLIDAYS = {(1, 1), (5, 1), (12, 25)}

_DAYS = "LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI"
_ROUNDS = (
    (_RECYCLING, r"COLLECTES\s+DU\s+TRI"),
    (_GENERAL, r"COLLECTES\s+DES\s+ORDURES\s+MENAGERES"),
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def map_commune(response: Any, *_keys: Any, commune: str, **_: Any) -> str:
    """The leaflet link of the map area titled ``commune``."""
    match = re.search(r"imageMapPro\((\{.*?\})\);", response.text[100_000:], re.DOTALL)
    if not match:
        raise ResponseShapeError("could not locate the imageMapPro config in the JS")
    links: dict[str, str] = {}
    titles: list[str] = []
    for spot in json.loads(match.group(1)).get("spots", []):
        title = spot.get("title", "")
        link = (spot.get("actions") or {}).get("link", "")
        if link.lower().endswith(".pdf"):
            links[_normalize(title)] = link
            titles.append(title)
    found = links.get(_normalize(commune))
    if found:
        return found
    wanted = _normalize(commune)
    names = [_normalize(t) for t in titles]
    close = difflib.get_close_matches(wanted, names, n=5, cutoff=0.5)
    raise SourceArgumentNotFoundWithSuggestions(
        "commune", commune, [titles[names.index(c)] for c in close]
    )


def leaflet_schedules(text: str, source: Any = None) -> list[tuple[str, int, str]]:
    """``(label, weekday, parity)`` for each round a leaflet's text states."""
    plain = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    ).upper()
    rounds = []
    for label, heading in _ROUNDS:
        match = re.search(
            heading
            + rf"\s*(?:TOUS\s+LES\s+)?({_DAYS})S?\s+SEMAINES?\s+(PAIRES|IMPAIRES)",
            plain,
        )
        if match:
            weekday = recurrence.weekday(match.group(1))
            parity = "even" if match.group(2) == "PAIRES" else "odd"
            if weekday is not None:
                rounds.append((label, weekday, parity))
    return rounds


def _describe(record: tuple[str, int, str], source: Any = None):
    label, weekday, parity = record
    yield Schedule(
        label,
        recurrence.next_weekday(weekday),
        count=53,
        iso_week_parity=parity,  # type: ignore[arg-type]
    )


def _defer(date: datetime.date, key: str, source: Any = None) -> datetime.date:
    if (date.month, date.day) in _DEFERRED_HOLIDAYS:
        return date + datetime.timedelta(days=1)
    return date


@final
class Source(BaseSource):
    TITLE = "SICTOM du Val de Saône"
    DESCRIPTION = (
        "Source for SICTOM du Val de Saône waste collection schedules in "
        "Haute-Saône, France."
    )
    URL = "https://www.sictomvds.com"
    COUNTRY = "fr"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@KingKemar"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Velleminfroy": {"commune": "Velleminfroy"},
        "Ancier": {"commune": "Ancier"},
        "Mantoche": {"commune": "Mantoche"},
    }

    PARAMS = (municipality("commune"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune as it is named on the map at "
            "https://www.sictomvds.com (for example 'Velleminfroy')."
        ),
        "fr": (
            "Saisissez votre commune telle qu'elle apparaît sur la carte de "
            "https://www.sictomvds.com (par exemple « Velleminfroy »)."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(Lookup(_JS_URL, pick=map_commune),),
        url=lambda leaflet, **_: leaflet,
        raise_for_status=True,
    )
    parse = PdfTextParser(min_chars=50)
    preprocess = Compose(
        leaflet_schedules,
        RecurrenceExpander(_describe),
        HolidayShift(_defer),
    )
    transform = ICSTransformer(
        type_value_map={_GENERAL: wt.GENERAL_WASTE, _RECYCLING: wt.RECYCLABLES}
    )
