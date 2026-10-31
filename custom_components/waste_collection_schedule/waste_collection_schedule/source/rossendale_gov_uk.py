"""Rossendale Borough Council (rossendale.gov.uk), UK.

The council's "Bin Collection Days" directory (Jadu) lists every property:

1. ``/directory/search?directoryID=10094&keywords=<postcode>`` returns the
   properties at a postcode, each linking to its directory record
   ("13 Albert Street Whitworth OL12 8PJ").
2. The record page links the property's zone calendar, a one-page PDF under
   ``/downloads/file/<id>/...`` (the same link serves each new April-March
   year, whatever its slug says).
3. The PDF prints two tables side by side, "GENERAL WASTE" and "RECYCLING
   WASTE", one row per month: the month name, a two-digit year and that month's
   collection days ("SEPTEMBER 26 8 22"). The rows are read by position with
   ``parsers.PdfTableParser``; a day belongs to the table whose heading is
   nearest to its left.

Garden waste is collected by subscription and not part of the calendar; the
weekly food caddy goes out on the general-waste and recycling days.
"""

import datetime
import re
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import PdfRow
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://www.rossendale.gov.uk"
SEARCH_URL = f"{BASE_URL}/directory/search"
DIRECTORY_ID = "10094"

_HEADINGS = ("GENERAL", "RECYCLING")
_LABELS = {"GENERAL": "General Waste", "RECYCLING": "Recycling"}
# "SEPTEMBER 26 8 22" -> month name, two-digit year, days.
_MONTH_ROW = re.compile(r"^([A-Za-z]+)\s+(\d{2})\s+((?:\d{1,2}\s*)+)$")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().upper()


def _record_url(
    response: Any, *_keys: Any, postcode: str, house_number: str, **_: Any
) -> str:
    """The directory record of the property at ``house_number``, ``postcode``."""
    soup = BeautifulSoup(response.text, "html.parser")
    records = {
        _norm(a.get_text(" ")): urljoin(BASE_URL, str(a["href"]))
        for a in soup.select('a[href*="/directory-record/"]')
    }
    if not records:
        raise SourceArgumentNotFound("postcode", postcode)
    wanted = _norm(str(house_number))
    for text, url in records.items():
        if text == wanted or text.startswith(f"{wanted} "):
            return url
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", house_number, sorted(records)
    )


def _calendar_url(response: Any, *_keys: Any, **_: Any) -> str:
    """The zone calendar linked from a directory record."""
    soup = BeautifulSoup(response.text, "html.parser")
    link = soup.select_one('dd a[href*="/downloads/file/"]')
    if link is None:
        raise ValueError("no zone calendar link on the directory record")
    return urljoin(BASE_URL, str(link["href"]))


def _rows(
    rows: list[PdfRow], source: BaseSource | None = None
) -> list[tuple[datetime.date, str]]:
    """(date, label) pairs from the two month-per-row tables."""
    headings: list[tuple[float, str]] = []
    entries: list[tuple[datetime.date, str]] = []
    for row in rows:
        found = [
            (w.x0, w.text.upper()) for w in row.words if w.text.upper() in _HEADINGS
        ]
        if found:
            headings = sorted(found)
            continue
        if not headings:
            continue
        blocks: dict[str, list[str]] = {}
        for word in row.words:
            left = [label for x, label in headings if x <= word.x0 + 5]
            label = left[-1] if left else headings[0][1]
            blocks.setdefault(label, []).append(word.text)
        for heading, texts in blocks.items():
            match = _MONTH_ROW.match(" ".join(" ".join(texts).split()))
            month = recurrence.month(match.group(1)) if match else None
            if not match or month is None:
                continue
            year = 2000 + int(match.group(2))
            for day in match.group(3).split():
                entries.append((datetime.date(year, month, int(day)), _LABELS[heading]))
    return entries


@final
class Source(BaseSource):
    TITLE = "Rossendale Borough Council"
    DESCRIPTION = "Source for Rossendale Borough Council, UK."
    URL = "https://www.rossendale.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "13 Albert Street, Whitworth": {
            "postcode": "OL12 8PJ",
            "house_number": "13",
        },
        "Feldspar, Eagley Bank, Shawforth": {
            "postcode": "OL12 8HE",
            "house_number": "Feldspar",
        },
        "8 Dearden Nook, Rawtenstall": {
            "postcode": "BB4 6BH",
            "house_number": "8",
        },
    }

    PARAMS = (postcode("postcode", "house_number"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your house number (or house name, as "
            "listed at https://www.rossendale.gov.uk/directory/10094/"
            "bin-collection-days)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                SEARCH_URL,
                params=lambda postcode, **_: {
                    "directoryID": DIRECTORY_ID,
                    "keywords": postcode,
                },
                pick=_record_url,
            ),
            retrievers.Lookup(lambda record_url, **_: record_url, pick=_calendar_url),
        ),
        url=lambda record_url, calendar_url, **_: calendar_url,
    )
    parse = parsers.PdfTableParser(min_words=30)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer()
