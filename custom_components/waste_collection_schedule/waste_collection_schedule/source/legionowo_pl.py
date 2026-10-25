"""Legionowo, Poland.

The city publishes one LibreOffice Calc PDF per street from
https://legionowo.pl/harmonogramy-odpady/. Each PDF is one year of month
grids: the day numbers are printed and a coloured cell is a collection. The
legend names the colour. A coloured frame around the same fill (blue in the
2026 sheets) is that waste plus a bin wash ("mycie pojemnika"). The year and
the weekday of every day number are checked against the grid, so a shifted
layout fails instead of moving the schedule.
"""

from __future__ import annotations

import datetime
import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Any, ClassVar, NamedTuple, final
from urllib.parse import quote

from bs4 import BeautifulSoup
from waste_collection_schedule import (
    lookups,
    parsers,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://legionowo.pl/harmonogramy-odpady/"
_PDF_PREFIX = "https://legionowo.pl/harmonogramy-odpady/pdf/"

_MIXED = "Odpady zmieszane"
_MIXED_WASH = "Odpady zmieszane i mycie pojemnika"
_GARDEN = "Odpady ogrodowe"
_BULKY = "Odpady wielkogabarytowe"
_BIO = "BIO odpady kuchenne"
_BIO_WASH = "BIO odpady kuchenne i mycie pojemnika"
_TREES = "Odbiór choinek"
_RECYCLING = "Odpady segregowane"

_TYPE_VALUE_MAP = {
    _MIXED: wt.GENERAL_WASTE,
    _MIXED_WASH: wt.GENERAL_WASTE,
    _GARDEN: wt.GARDEN_WASTE,
    _BULKY: wt.BULKY_WASTE,
    _BIO: wt.FOOD_WASTE,
    _BIO_WASH: wt.FOOD_WASTE,
    _TREES: wt.GARDEN_WASTE,
    _RECYCLING: wt.RECYCLABLES,
}

# A calendar cell and its legend swatch are this size; month and weekday bars
# are the full column and are ignored.
_CELL_MIN = 8.0
_CELL_MAX_W = 40.0
_CELL_MAX_H = 20.0
# How far a printed month name may sit from a day number in the same column.
_MONTH_X = 100.0
# Per-channel distance at which a cell fill still counts as a legend colour.
# The bulky swatch is a near-black (0.067) while some day cells are pure black.
_COLOUR_TOLERANCE = 0.12
_PREFIXES = ("ulica ", "ul ", "aleja ", "al ")


class _Paint(NamedTuple):
    colour: tuple[float, ...]
    framed: bool
    label: str


def _street_links(response: Any) -> dict[str, str]:
    """Visible street name to its PDF URL, as listed on the index page."""
    links: dict[str, str] = {}
    for item in BeautifulSoup(response.text, "html.parser").select("li[data-file]"):
        label = " ".join(item.get_text(" ", strip=True).split())
        filename = str(item.get("data-file") or "").strip()
        if label and filename:
            links[label] = _PDF_PREFIX + quote(filename)
    response_shape.expect(
        bool(links),
        source_name="legionowo_pl",
        detail="no street list on the schedule page",
        raw=getattr(response, "text", "")[:500],
    )
    return links


def _match_street(links: dict[str, str], wanted: str) -> str | None:
    """The PDF URL for ``wanted``, or None when nothing matches.

    An exact name wins. Otherwise a name that contains ``wanted`` is used when
    it is the only one ("Senator" is Senatorska); several hits stay ambiguous
    ("Legionów" is both number ranges).
    """
    exact = [
        url for name, url in links.items() if lookups.normalize_loose(name) == wanted
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        names = [name for name in links if lookups.normalize_loose(name) == wanted]
        raise SourceArgAmbiguousWithSuggestions("street", wanted, sorted(names))
    partial = {
        name: url
        for name, url in links.items()
        if wanted and wanted in lookups.normalize_loose(name)
    }
    if len(partial) == 1:
        return next(iter(partial.values()))
    if partial:
        raise SourceArgAmbiguousWithSuggestions("street", wanted, sorted(partial))
    return None


def _pdf_url(response: Any, street: str = "", **_: Any) -> str:
    links = _street_links(response)
    wanted = lookups.normalize_loose(street)
    found = _match_street(links, wanted)
    if found is None:
        stripped = wanted
        for prefix in _PREFIXES:
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix) :]
                break
        if stripped != wanted:
            found = _match_street(links, stripped)
    if found is None:
        raise SourceArgumentNotFoundWithSuggestions("street", street, sorted(links))
    return found


def _cell(vector: parsers.PdfVector) -> bool:
    """A day-sized fill. Near-white rectangles are empty padding, not collections."""
    width = vector.x1 - vector.x0
    height = vector.y1 - vector.y0
    colour = vector.fill_color
    if colour is not None and len(colour) >= 3 and min(colour[:3]) >= 0.97:
        return False
    return (
        colour is not None
        and _CELL_MIN < width < _CELL_MAX_W
        and _CELL_MIN < height < _CELL_MAX_H
    )


def _marker(colour: tuple[float, ...] | None) -> bool:
    """A stroke colour that paints a frame rather than a black grid line."""
    if colour is None or len(colour) < 3:
        return False
    red, green, blue = colour[:3]
    return (
        max(red, green, blue) >= 0.25
        and max(red, green, blue) - min(red, green, blue) >= 0.15
    )


def _framed(cell: parsers.PdfVector, strokes: list[parsers.PdfVector]) -> bool:
    """True when a coloured frame runs along at least three edges of ``cell``.

    A frame is drawn on the cell border, so one edge is shared with the
    neighbour. Requiring three sides keeps that neighbour unframed.
    """
    sides: set[str] = set()
    for stroke in strokes:
        if not _marker(stroke.stroke_color):
            continue
        cx = (stroke.x0 + stroke.x1) / 2
        cy = (stroke.y0 + stroke.y1) / 2
        vertical = stroke.y1 - stroke.y0 > stroke.x1 - stroke.x0
        if vertical:
            overlap = min(stroke.y1, cell.y1) - max(stroke.y0, cell.y0)
            if overlap <= _CELL_MIN:
                continue
            if abs(cx - cell.x0) < 3:
                sides.add("L")
            elif abs(cx - cell.x1) < 3:
                sides.add("R")
        else:
            overlap = min(stroke.x1, cell.x1) - max(stroke.x0, cell.x0)
            if overlap <= _CELL_MIN:
                continue
            if abs(cy - cell.y1) < 3:
                sides.add("T")
            elif abs(cy - cell.y0) < 3:
                sides.add("B")
    return len(sides) >= 3


def _contains(cell: parsers.PdfVector, word: parsers.PdfTextFragment) -> bool:
    return cell.x0 <= word.x <= cell.x1 and cell.y0 <= word.y <= cell.y1


def _distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        return 1.0
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def _classify(text: str) -> str | None:
    """The stable label for one legend entry. More specific phrases win."""
    folded = lookups.normalize_loose(text)
    wash = "mycie" in folded
    # "choinek" (genitive) does not contain the stem "choink".
    if "choin" in folded:
        return _TREES
    if "gabaryt" in folded:
        return _BULKY
    if "segregow" in folded:
        return _RECYCLING
    if "ogrodow" in folded or "roslinn" in folded:
        return _GARDEN
    if "kuchenn" in folded or folded.startswith("bio"):
        return _BIO_WASH if wash else _BIO
    if "zmieszan" in folded:
        return _MIXED_WASH if wash else _MIXED
    return None


def _legend_lines(
    words: list[parsers.PdfTextFragment],
    swatch: parsers.PdfVector,
    floor: float,
    right: float,
) -> str:
    """The legend text to the right of ``swatch``, down to ``floor``."""
    chosen = [
        word
        for word in words
        if swatch.x1 - 2 < word.x < right and floor < word.y <= swatch.y1 + 2
    ]
    rows: list[list[parsers.PdfTextFragment]] = []
    for word in sorted(chosen, key=lambda item: -item.y):
        if rows and abs(rows[-1][0].y - word.y) <= 3:
            rows[-1].append(word)
        else:
            rows.append([word])
    return " ".join(
        " ".join(word.text for word in sorted(row, key=lambda item: item.x))
        for row in rows
    ).strip()


def _legend(
    layout: parsers.PdfWordLayout,
    cells: list[parsers.PdfVector],
    strokes: list[parsers.PdfVector],
    legend_y: float,
    source_name: str,
) -> list[_Paint]:
    swatches = [cell for cell in cells if (cell.y0 + cell.y1) / 2 < legend_y]
    response_shape.expect(
        len(swatches) >= 4,
        source_name=source_name,
        detail=f"legend has {len(swatches)} colour swatches, expected at least 4",
        raw=str(layout.lines[-8:]),
    )
    columns: list[list[parsers.PdfVector]] = []
    for swatch in sorted(swatches, key=lambda cell: cell.x0):
        if columns and swatch.x0 - columns[-1][0].x0 < 40:
            columns[-1].append(swatch)
        else:
            columns.append([swatch])
    paints: list[_Paint] = []
    for index, column in enumerate(columns):
        right = columns[index + 1][0].x0 - 1 if index + 1 < len(columns) else 1e9
        ordered = sorted(column, key=lambda cell: -cell.y0)
        for position, swatch in enumerate(ordered):
            if position + 1 < len(ordered):
                floor = ordered[position + 1].y1
            else:
                floor = swatch.y0 - 18
            text = _legend_lines(layout.words, swatch, floor, right)
            label = _classify(text)
            response_shape.expect(
                label is not None,
                source_name=source_name,
                detail=f"unrecognised legend entry {text!r}",
                raw=str(layout.lines[-12:]),
            )
            if label is None:
                continue
            colour = tuple(swatch.fill_color or ())
            paints.append(_Paint(colour, _framed(swatch, strokes), label))
    seen: set[tuple[tuple[float, ...], bool]] = set()
    for paint in paints:
        key = (tuple(round(channel, 3) for channel in paint.colour), paint.framed)
        response_shape.expect(
            key not in seen,
            source_name=source_name,
            detail=f"legend repeats {paint.label}",
            raw=str(paints),
        )
        seen.add(key)
    return paints


def _label_for(
    colour: tuple[float, ...], framed: bool, paints: list[_Paint], source_name: str
) -> str:
    pool = [paint for paint in paints if paint.framed is framed]
    response_shape.expect(
        bool(pool),
        source_name=source_name,
        detail="legend has no swatch for a framed cell" if framed else "empty legend",
    )
    ranked = sorted(pool, key=lambda paint: _distance(colour, paint.colour))
    best = _distance(colour, ranked[0].colour)
    response_shape.expect(
        best <= _COLOUR_TOLERANCE
        and (len(ranked) == 1 or _distance(colour, ranked[1].colour) - best > 0.02),
        source_name=source_name,
        detail=f"cell colour {tuple(round(c, 3) for c in colour)} matches no legend entry",
        raw=str(ranked[:3]),
    )
    return ranked[0].label


def _months(
    layout: parsers.PdfWordLayout, source_name: str
) -> dict[int, parsers.PdfTextFragment]:
    found: dict[int, parsers.PdfTextFragment] = {}
    for word in layout.words:
        month = recurrence.month(word.text)
        if month is None:
            continue
        response_shape.expect(
            month not in found,
            source_name=source_name,
            detail=f"month {month} is printed more than once",
            raw=word.text,
        )
        found[month] = word
    response_shape.expect(
        set(found) == set(range(1, 13)),
        source_name=source_name,
        detail=f"expected 12 month headings, found {sorted(found)}",
        raw=str(layout.lines[:15]),
    )
    return found


def _year(layout: parsers.PdfWordLayout, source_name: str) -> int:
    years = {
        int(year)
        for year in re.findall(
            r"\b(20\d\d)\b", " ".join(line.text for line in layout.lines)
        )
    }
    response_shape.expect(
        len(years) == 1,
        source_name=source_name,
        detail=f"expected one calendar year in the PDF, found {sorted(years)}",
        raw=str(layout.lines[:5]),
    )
    return next(iter(years))


def _columns(xs: list[float]) -> list[float]:
    centres: list[float] = []
    for x in sorted(xs):
        if not centres or x - centres[-1] > 8:
            centres.append(x)
        else:
            centres[-1] = (centres[-1] + x) / 2
    return centres


def _collections(
    layouts: list[parsers.PdfWordLayout], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    source_name = response_shape.source_name(source)
    response_shape.expect(
        len(layouts) == 1,
        source_name=source_name,
        detail=f"expected one PDF, got {len(layouts)}",
    )
    layout = layouts[0]
    year = _year(layout, source_name)
    months = _months(layout, source_name)
    legend_lines = [line for line in layout.lines if "legenda" in line.text.casefold()]
    response_shape.expect(
        len(legend_lines) == 1,
        source_name=source_name,
        detail="schedule PDF has no legend heading",
        raw=str(layout.lines[-8:]),
    )
    legend_y = legend_lines[0].y
    cells = [vector for vector in layout.vectors if _cell(vector)]
    strokes = [vector for vector in layout.vectors if vector.fill_color is None]
    paints = _legend(layout, cells, strokes, legend_y, source_name)

    by_month: dict[int, list[parsers.PdfTextFragment]] = defaultdict(list)
    for word in layout.words:
        if word.y <= legend_y or not re.fullmatch(r"\d{1,2}", word.text):
            continue
        day = int(word.text)
        if not 1 <= day <= 31:
            continue
        above = [
            month
            for month, heading in months.items()
            if heading.y > word.y + 8 and abs(heading.x - word.x) < _MONTH_X
        ]
        if not above:
            continue
        by_month[min(above, key=lambda month: months[month].y - word.y)].append(word)

    dated: list[tuple[datetime.date, parsers.PdfTextFragment]] = []
    for month, words in sorted(by_month.items()):
        centres = _columns([word.x for word in words])
        response_shape.expect(
            len(centres) == 7,
            source_name=source_name,
            detail=f"month {month} has {len(centres)} weekday columns, expected 7",
            raw=str(centres),
        )
        for word in words:
            column = min(range(len(centres)), key=lambda i: abs(centres[i] - word.x))
            try:
                found = datetime.date(year, month, int(word.text))
            except ValueError:
                response_shape.expect(
                    False,
                    source_name=source_name,
                    detail=f"invalid day {word.text} in month {month}",
                )
                return
            response_shape.expect(
                found.weekday() == column,
                source_name=source_name,
                detail=(
                    f"{found.isoformat()} is weekday {found.weekday()} but sits in "
                    f"column {column}"
                ),
                raw=word.text,
            )
            dated.append((found, word))

    calendar_cells = [cell for cell in cells if (cell.y0 + cell.y1) / 2 > legend_y]
    used: set[int] = set()
    for found, word in dated:
        cell = next((item for item in calendar_cells if _contains(item, word)), None)
        if cell is None:
            continue
        used.add(id(cell))
        colour = tuple(cell.fill_color or ())
        yield found, _label_for(colour, _framed(cell, strokes), paints, source_name)
    missing = [cell for cell in calendar_cells if id(cell) not in used]
    response_shape.expect(
        not missing,
        source_name=source_name,
        detail=f"{len(missing)} coloured day cells contain no day number",
        raw=str(missing[:5]),
    )


@final
class Source(BaseSource):
    TITLE = "Legionowo"
    DESCRIPTION = "Source for Legionowo, Poland waste collection schedules."
    URL = _INDEX_URL
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Senatorska": {"street": "Senatorska"},
    }

    PARAMS = (street(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street as listed on "
            "https://legionowo.pl/harmonogramy-odpady/ (for example "
            "'Senatorska'). Where a street is split by house number, include "
            "the range exactly as shown, such as 'Aleja Legionów do nr 75' or "
            "'Aleja Legionów od nr 76'. Accents and a leading 'ul.' are ignored."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_INDEX_URL, pick=_pdf_url, encoding="utf-8", timeout=120),
        ),
        url=lambda pdf_url, **_: pdf_url,
        raise_for_status=True,
        # The street PDF is small but the host often trickles it out.
        timeout=180,
    )
    parse = parsers.PdfWordLayoutParser(
        min_words=300, min_vectors=40, include_strokes=True
    )
    preprocess = staticmethod(_collections)
    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP, carry_raw_label=True)
