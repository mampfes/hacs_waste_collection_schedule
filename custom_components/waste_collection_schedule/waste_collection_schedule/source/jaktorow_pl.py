"""Gmina Jaktorów, Poland.

The municipality publishes one yearly schedule PDF (operated by PreZero) with a
page per collection region ("rejon"): the region's villages and streets, then a
table with a row per waste type and a column per month, each cell listing the
collection days. The table text sits inside Form XObjects, so it is read with
``PdfWordLayoutParser(include_form_text=True)``; the preprocessor bins the day
numbers into the month columns named in the header row and into the waste-type
row whose label sits nearest vertically.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import (
    config_params,
    lookups,
    parsers,
    recurrence,
    response_shape,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

MIXED = "Komunalne"
SELECTIVE = "Segregowane"
PAPER = "Papier"
GLASS = "Szkło"
GREEN = "Odpady zielone"
BULKY = "Gabaryty, gruz, chemikalia"
TYRES = "Opony"

# Row labels as printed in the table's first column, matched as lowercase
# substrings of a label line, first match wins.
_ROW_LABELS = (
    ("komunalne", MIXED),
    ("segregowane", SELECTIVE),
    ("papier", PAPER),
    ("szkło", GLASS),
    ("zielone", GREEN),
    ("gabaryty", BULKY),
    ("opony", TYRES),
)

_REGIONS = {f"Rejon {number}": number for number in range(1, 9)}

# A day cell's text sits within this distance (points) of its row label.
_ROW_TOLERANCE = 12.0

_DAYS_RE = re.compile(r"\d{1,2}(?:,\d{0,2})*")


def _row_label(text: str) -> str | None:
    lowered = text.lower()
    return next((label for key, label in _ROW_LABELS if key in lowered), None)


def _month_columns(
    words: list[parsers.PdfTextFragment],
) -> tuple[float, list[float]] | None:
    """The header row's y and the x centre of each of the twelve month columns.

    The header prints the month names letter-spaced, so a name can arrive split
    ("STY" "CZEŃ", "KW" "IECIEŃ") or glued to its neighbour
    ("PAŹDZIERNIKLIST" "OPAD"). Fragments are joined greedily into month names;
    a month that cannot be recovered that way is interpolated from its
    neighbours.
    """
    rows: dict[int, list[parsers.PdfTextFragment]] = {}
    for word in words:
        rows.setdefault(round(word.y), []).append(word)
    for y, row in sorted(rows.items(), reverse=True):
        row.sort(key=lambda word: word.x)
        found: dict[int, float] = {}
        start = 0
        while start < len(row):
            for end in range(min(len(row), start + 3), start, -1):
                month = recurrence.month("".join(w.text for w in row[start:end]))
                if month is not None and month not in found:
                    found[month] = sum(w.x for w in row[start:end]) / (end - start)
                    start = end
                    break
            else:
                start += 1
        if len(found) < 8 or 1 not in found or 12 not in found:
            continue
        known = sorted(found)
        centres = []
        for month in range(1, 13):
            if month in found:
                centres.append(found[month])
                continue
            before = max(m for m in known if m < month)
            after = min(m for m in known if m > month)
            share = (month - before) / (after - before)
            centres.append(found[before] + share * (found[after] - found[before]))
        return float(y), centres
    return None


def _rows(
    layouts: list[parsers.PdfWordLayout], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    region = lookups.resolve(
        _REGIONS,
        source.params["region"] if source else "",
        argument="region",
    )
    name = response_shape.source_name(source)
    layout = layouts[0]

    page = next(
        (
            line.page
            for line in layout.lines
            if re.fullmatch(rf"REJON\s+{region}", line.text.strip())
        ),
        None,
    )
    response_shape.expect(
        page is not None,
        source_name=name,
        detail=f"no page for REJON {region} in the schedule PDF",
        raw=str(layout.lines[:10]),
    )
    lines = [line for line in layout.lines if line.page == page]
    words = [word for word in layout.words if word.page == page]

    year_match = re.search(r"W ROKU (\d{4})", " ".join(line.text for line in lines))
    year = int(year_match.group(1)) if year_match else datetime.date.today().year

    header = _month_columns(words)
    response_shape.expect(
        header is not None,
        source_name=name,
        detail=f"no month header row on the REJON {region} page",
        raw=str(lines[:20]),
    )
    if header is None:
        return
    header_y, centres = header
    half = (centres[1] - centres[0]) / 2
    left, right = centres[0] - half, centres[-1] + half

    anchors = [
        (line.y, label)
        for line in lines
        if line.x < left
        and line.y < header_y
        and (label := _row_label(line.text)) is not None
    ]
    response_shape.expect(
        bool(anchors),
        source_name=name,
        detail=f"no waste-type labels on the REJON {region} page",
        raw=str(lines[:20]),
    )

    cells: dict[tuple[str, int], list[str]] = {}
    for word in words:
        if not left <= word.x <= right or word.y >= header_y - 3:
            continue
        if not _DAYS_RE.fullmatch(word.text):
            continue
        anchor_y, label = min(anchors, key=lambda anchor: abs(anchor[0] - word.y))
        if abs(anchor_y - word.y) > _ROW_TOLERANCE:
            continue
        month = min(range(12), key=lambda i: abs(centres[i] - word.x)) + 1
        cells.setdefault((label, month), []).append(word.text)

    for (label, month), texts in cells.items():
        for day in re.findall(r"\d+", ",".join(texts)):
            try:
                yield datetime.date(year, month, int(day)), label
            except ValueError:
                continue


@final
class Source(BaseSource):
    TITLE = "Gmina Jaktorów"
    DESCRIPTION = "Source for Gmina Jaktorów waste collection schedule (Poland)"
    URL = "https://bip.jaktorow.pl/odpady-komunalne/harmonogram"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rejon 2": {"region": "Rejon 2"},
        "Rejon 6 (Henryszew)": {"region": "Rejon 6"},
    }

    PARAMS = (config_params.dropdown("region", list(_REGIONS), label="Region"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your collection region (rejon). Most villages are split "
            "across regions by street: the schedule PDF linked on "
            "https://bip.jaktorow.pl/odpady-komunalne/harmonogram lists the "
            "villages and streets of each region at the top of its page (for "
            "example, all of Henryszew is in Rejon 6)."
        ),
    }

    retrieve = PdfLinkRetriever(
        index_url="https://bip.jaktorow.pl/odpady-komunalne/harmonogram",
        pattern=r"harmonogram(\d{4})\.pdf",
    )
    parse = parsers.PdfWordLayoutParser(min_words=500, include_form_text=True)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            MIXED: wt.GENERAL_WASTE,
            SELECTIVE: wt.RECYCLABLES,
            PAPER: wt.PAPER,
            GLASS: wt.GLASS,
            GREEN: wt.GARDEN_WASTE,
            BULKY: wt.BULKY_WASTE,
            TYRES: wt.OTHER,
        }
    )
