"""Gemeinde Arlesheim (BL), Switzerland.

Arlesheim publishes a yearly "Abfallkalender" PDF. One page ("Abfuhrdaten")
holds a table with one block of rows per collection (Kehricht West/Ost,
Karton, Altpapier, Grünabfuhr, Häcksel) and one column per month, each cell
listing the day numbers. Holiday shifts are already printed as the shifted
date (marked ``*`` or ``+``). A row block's vertical centre is marked by the
collecting company in the right-most "Firma" column; shaded blocks also carry
a filled label rectangle on the left, which is used first.
"""

import re
import unicodedata
from collections.abc import Iterable
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://www.arlesheim.ch/de/abfallwirtschaft/abfallkalender/"

KEHRICHT = "Kehricht und Sperrgut brennbar"
KARTON = "Karton"
ALTPAPIER = "Altpapier"
GRUEN = "Grünabfuhr"
HAECKSEL = "Häcksel"

_ROW_TITLES = (KEHRICHT, KARTON, ALTPAPIER, GRUEN, HAECKSEL)
_DAY_RE = re.compile(r"^(\d{1,2})[*+]?$")
_YEAR_RE = re.compile(r"Abfuhrdaten\s+(20\d\d)")
_TITLE_MAX_X = 165.0
_MAX_COLUMN_DISTANCE = 17.0
_MAX_ANCHOR_DISTANCE = 21.0  # 1.5 table rows


def _norm(text: str) -> str:
    # The PDF stores umlauts decomposed ("a" + combining diaeresis).
    return unicodedata.normalize("NFC", text)


def _row_label(
    title_lines: list[parsers.PdfTextFragment], y0: float, y1: float
) -> str | None:
    text = " ".join(_norm(t.text) for t in title_lines if y0 <= t.y <= y1)
    for title in _ROW_TITLES:
        if text.startswith(title):
            if title == KEHRICHT:
                if "West" in text:
                    return f"{KEHRICHT} West"
                if "Ost" in text:
                    return f"{KEHRICHT} Ost"
                return None
            return title
    return None


def collection_rows(
    layouts: list[parsers.PdfWordLayout], source: BaseSource
) -> Iterable[tuple[date, str]]:
    (layout,) = layouts
    name = response_shape.source_name(source)
    pages = [
        line.page for line in layout.lines if _YEAR_RE.match(line.text) is not None
    ]
    response_shape.expect(
        bool(pages),
        source_name=name,
        detail='no "Abfuhrdaten <year>" table page found in the PDF',
        raw=str(layout.lines[:10]),
    )
    page = pages[0]
    year_match = next(
        _YEAR_RE.match(line.text)
        for line in layout.lines
        if line.page == page and _YEAR_RE.match(line.text)
    )
    assert year_match is not None
    year = int(year_match.group(1))

    words = [w for w in layout.words if w.page == page]
    # Month names also occur in the footnotes ("25. Mai"); keep the header row.
    jan = [w for w in words if w.text == "Jan"]
    response_shape.expect(
        bool(jan),
        source_name=name,
        detail="could not find the month header row",
        raw=str([w.text for w in words[:40]]),
    )
    header_y = max(w.y for w in jan)
    headers = sorted(
        (w.x, month)
        for w in words
        if abs(w.y - header_y) < 2
        and (month := recurrence.month(_norm(w.text), "de", abbreviated=True))
    )
    response_shape.expect(
        len(headers) == 12,
        source_name=name,
        detail="could not find the twelve month columns",
        raw=str([w.text for w in words[:40]]),
    )
    first_x = headers[0][0] - _MAX_COLUMN_DISTANCE
    last_x = headers[-1][0] + _MAX_COLUMN_DISTANCE
    titles = [
        line for line in layout.lines if line.page == page and line.x < _TITLE_MAX_X
    ]

    # 1. Shaded blocks: filled label rectangle left of the month columns.
    bands: list[tuple[float, float, str]] = []
    for vec in layout.vectors:
        if vec.page != page or vec.x1 > first_x or vec.y1 > header_y:
            continue
        label = _row_label(titles, vec.y0, vec.y1)
        if label is not None:
            bands.append((vec.y0, vec.y1, label))
    banded = {label for _, _, label in bands}

    # 2. Unshaded blocks: anchored at the company name in the "Firma" column.
    anchors: list[tuple[float, str]] = []
    for w in words:
        if w.x <= last_x or w.y >= header_y or w.text == "Firma":
            continue
        nearest = min(titles, key=lambda t: abs(t.y - w.y), default=None)
        if nearest is None or abs(nearest.y - w.y) > 1.5:
            continue
        label = _row_label(titles, nearest.y - 1.5, nearest.y + 1.5)
        if label is not None and label not in banded:
            anchors.append((w.y, label))

    events: set[tuple[date, str]] = set()
    for w in words:
        if w.y >= header_y or not first_x <= w.x <= last_x:
            continue
        m = _DAY_RE.match(w.text)
        if m is None:
            continue
        label = next((lab for y0, y1, lab in bands if y0 <= w.y <= y1), None)
        if label is None and anchors:
            anchor_y, anchor = min(anchors, key=lambda a: abs(a[0] - w.y))
            # Stay within the anchored block (skips e.g. the page number).
            if abs(anchor_y - w.y) <= _MAX_ANCHOR_DISTANCE:
                label = anchor
        if label is None:
            continue
        month_x, month = min(headers, key=lambda h: abs(h[0] - w.x))
        if abs(month_x - w.x) > _MAX_COLUMN_DISTANCE:
            continue
        try:
            events.add((date(year, month, int(m.group(1))), label))
        except ValueError:
            continue

    response_shape.expect(
        bool(events),
        source_name=name,
        detail="no collection dates found in the Abfuhrdaten table",
        raw=str([w.text for w in words[:40]]),
    )
    kreis = str(source.params.get("kreis", "")).strip() if source else ""
    for collection_date, label in sorted(events):
        if label.startswith(KEHRICHT):
            if label != f"{KEHRICHT} {kreis}":
                continue
            label = KEHRICHT
        yield collection_date, label


@final
class Source(BaseSource):
    TITLE = "Gemeinde Arlesheim"
    DESCRIPTION = (
        "Source for waste collection in Arlesheim, Basel-Landschaft, Switzerland."
    )
    URL = "https://www.arlesheim.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kreis West": {"kreis": "West"},
        "Kreis Ost": {"kreis": "Ost"},
    }

    PARAMS = (dropdown("kreis", options=["West", "Ost"], label="Abfuhrkreis"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Pick your collection district (Kreis West: Monday, Kreis Ost: Thursday) from the map in the Abfallkalender PDF.",
        "de": "Wähle deinen Abfuhrkreis (Kreis West: Montag, Kreis Ost: Donnerstag) gemäss Plan im Abfallkalender-PDF.",
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_INDEX_URL, pattern=r"Abfallkalender.*\.pdf", select="first"
    )
    parse = parsers.PdfWordLayoutParser(min_words=50)
    preprocess = staticmethod(collection_rows)
    transform = ICSTransformer(
        type_value_map={
            KEHRICHT: wt.GENERAL_WASTE,
            KARTON: wt.PAPER,
            ALTPAPIER: wt.PAPER,
            GRUEN: wt.GARDEN_WASTE,
            HAECKSEL: wt.GARDEN_WASTE,
        }
    )
