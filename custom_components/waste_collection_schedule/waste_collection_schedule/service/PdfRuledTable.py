"""Pipeline component for waste tables printed with ruling lines in a text PDF.

Some providers publish a table (rows of areas or streets, a column per waste
round) whose multi-line cells plain text extraction interleaves with their
neighbours: ``pypdf`` and a line-by-line ``pdfminer`` pass both emit the second
line of one cell before the first line of the next. The table's grid is drawn
though, as thin filled rectangles (Word's cell borders), and that geometry is
unambiguous: every vertical rule is a column edge, every horizontal rule a row
edge, and a character belongs to the cell its centre falls into.

:class:`RuledTableParser` reads exactly that and hands back each page's table as
a grid of cell strings, plus the document text (for a year printed in the
title). What the columns mean (finding the header row, naming the rounds,
turning "wtorek, piątek" into dates) stays with the source, which reads the
grid with plain Python::

    parse = RuledTableParser(min_cells=20)

    def preprocess(self, document, source):
        for grid in document.grids:
            ...

The parser is purely geometric: it needs at least three vertical and three
horizontal rules per page to call it a table, and a page with fewer simply
yields no grid.

Some generators draw no page-wide rules at all, only a short border segment per
cell, and merge cells (an area name spanning the rows of all its rounds). For
those, ``RuledTableParser(merged_cells=True)`` takes every border segment as an
edge and repeats a merged cell's text in each row it spans: a cell continues
into the row below wherever no segment closes it, so each grid row reads as a
complete record. Each grid's page text is kept in ``page_texts`` alongside it,
for a page whose title names what its table is for.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule import response_shape
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Iterator

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Response

Grid = list[list[str]]

# A rule is a filled rectangle thinner than this (PDF points) in one direction
# and longer than the minimum in the other.
_RULE_THICKNESS = 3.0
_MIN_VERTICAL_RULE = 20.0
_MIN_HORIZONTAL_RULE = 200.0
# A border drawn cell by cell is a run of segments at least this long.
_MIN_SEGMENT = 5.0
# Rules closer together than this are one edge (a border drawn as two strokes).
_EDGE_TOLERANCE = 3.0
# Characters within this many points vertically are on one line of a cell.
_LINE_HEIGHT = 3.0
# A horizontal gap wider than this between characters is a space.
_WORD_GAP = 1.0


class RuledTables(NamedTuple):
    """The document text and one grid of cell strings per page that has a table.

    ``page_texts`` holds the text of each grid's page, in the order of
    ``grids``; it is filled by ``RuledTableParser(merged_cells=True)``.
    """

    text: str
    grids: list[Grid]
    page_texts: tuple[str, ...] = ()


def collapse_edges(
    values: list[float], tolerance: float = _EDGE_TOLERANCE
) -> list[float]:
    """Sort ``values`` and merge those within ``tolerance`` of the previous edge."""
    edges: list[float] = []
    for value in sorted(values):
        if not edges or value - edges[-1] > tolerance:
            edges.append(value)
    return edges


def cell_text(chars: list[Any]) -> str:
    """Join the characters of one cell (pdfminer ``LTChar``) into single-spaced text.

    Characters are read top to bottom, then left to right; a change of line or a
    horizontal gap starts a new word. Whitespace glyphs are dropped: an Excel
    PDF paints a cell's padding as space characters that overlap the real
    glyphs, and sorting those by x splits a day number ("11" comes out "1 1").
    A real word space is still a gap between the glyphs on either side.
    """
    ordered = sorted(
        (char for char in chars if not char.get_text().isspace()),
        key=lambda c: (-round(c.y0 / _LINE_HEIGHT), c.x0),
    )
    out = ""
    prev = None
    for char in ordered:
        if prev is not None and (
            round(char.y0 / _LINE_HEIGHT) != round(prev.y0 / _LINE_HEIGHT)
            or char.x0 - prev.x1 > _WORD_GAP
        ):
            out += " "
        out += char.get_text()
        prev = char
    return " ".join(out.split())


def locate(
    edges: list[float], centre: float, *, descending: bool = False
) -> int | None:
    """The index of the band of ``edges`` containing ``centre``, or None.

    ``edges`` ascend for columns; pass ``descending=True`` for rows, whose edges
    run top to bottom (decreasing y).
    """
    for i in range(len(edges) - 1):
        if descending:
            if edges[i] >= centre > edges[i + 1]:
                return i
        elif edges[i] <= centre < edges[i + 1]:
            return i
    return None


def _walk(obj: Any) -> Iterator[Any]:
    yield obj
    if hasattr(obj, "__iter__"):
        for child in obj:
            yield from _walk(child)


def page_grid(page: Any) -> Grid | None:
    """The ruled table of one pdfminer page layout, or None when it has none."""
    from pdfminer.layout import LTChar, LTCurve

    objs = list(_walk(page))
    chars = [o for o in objs if isinstance(o, LTChar)]
    rules = [o for o in objs if isinstance(o, LTCurve)]
    xs = collapse_edges(
        [
            r.x0
            for r in rules
            if r.height > _MIN_VERTICAL_RULE and r.width < _RULE_THICKNESS
        ]
    )
    ys = collapse_edges(
        [
            r.y0
            for r in rules
            if r.width > _MIN_HORIZONTAL_RULE and r.height < _RULE_THICKNESS
        ]
    )[::-1]
    if len(xs) < 3 or len(ys) < 3:
        return None

    cells: dict[tuple[int, int], list[Any]] = {}
    for char in chars:
        col = locate(xs, (char.x0 + char.x1) / 2)
        row = locate(ys, (char.y0 + char.y1) / 2, descending=True)
        if col is not None and row is not None:
            cells.setdefault((row, col), []).append(char)
    return [
        [cell_text(cells.get((r, c), [])) for c in range(len(xs) - 1)]
        for r in range(len(ys) - 1)
    ]


def merged_page_grid(page: Any) -> Grid | None:
    """The table of a page drawn with per-cell border segments, merged cells filled.

    Every border segment (a filled rectangle longer than ``_MIN_SEGMENT``) is an
    edge; a cell runs on into the row below unless a horizontal segment crosses
    its column at that edge, and its text is repeated in every row it spans.
    """
    from pdfminer.layout import LTChar, LTCurve

    objs = list(_walk(page))
    chars = [o for o in objs if isinstance(o, LTChar) and not o.get_text().isspace()]
    rules = [o for o in objs if isinstance(o, LTCurve)]
    horizontal = [
        r for r in rules if r.width > _MIN_SEGMENT and r.height < _RULE_THICKNESS
    ]
    xs = collapse_edges(
        [r.x0 for r in rules if r.height > _MIN_SEGMENT and r.width < _RULE_THICKNESS]
    )
    ys = collapse_edges([r.y0 for r in horizontal])[::-1]
    if len(xs) < 3 or len(ys) < 3:
        return None

    def closed(y: float, x: float) -> bool:
        return any(
            abs(r.y0 - y) <= _EDGE_TOLERANCE and r.x0 - 1 <= x <= r.x1 + 1
            for r in horizontal
        )

    cells: dict[tuple[int, int], list[Any]] = {}
    for char in chars:
        col = locate(xs, (char.x0 + char.x1) / 2)
        row = locate(ys, (char.y0 + char.y1) / 2, descending=True)
        if col is not None and row is not None:
            cells.setdefault((row, col), []).append(char)

    n_rows, n_cols = len(ys) - 1, len(xs) - 1
    grid: Grid = [[""] * n_cols for _ in range(n_rows)]
    for col in range(n_cols):
        centre = (xs[col] + xs[col + 1]) / 2
        row = 0
        while row < n_rows:
            first, span = row, list(cells.get((row, col), []))
            while row + 1 < n_rows and not closed(ys[row + 1], centre):
                row += 1
                span += cells.get((row, col), [])
            text = cell_text(span)
            for spanned in range(first, row + 1):
                grid[spanned][col] = text
            row += 1
    return grid


def merge_split_rows(
    rows: list[list[str]], key_columns: tuple[int, ...]
) -> list[list[str]]:
    """Merge a row whose ``key_columns`` are all empty into the row above it.

    A stray ruling line can cut one table row in two; the lower half has no
    area or street of its own, only the tail of the other cells.
    """
    merged: list[list[str]] = []
    for cols in rows:
        if not any(cols):
            continue
        if merged and not any(cols[c] for c in key_columns):
            merged[-1] = [
                " ".join(filter(None, (a, b)))
                for a, b in zip(merged[-1], cols, strict=True)
            ]
            continue
        merged.append(cols)
    return merged


class RuledTableParser(Parser[RuledTables]):
    """Read the ruled tables of a text PDF (pdfminer.six) as grids of cell text.

    Args:
        min_cells: minimum number of non-empty cells across all grids; fewer
            (a scan, or a page whose borders are no longer drawn) is logged and
            raises ``ResponseShapeError`` rather than yielding nothing.
        merged_cells: read tables drawn with per-cell border segments and
            merged cells (see :func:`merged_page_grid`), and keep each grid's
            page text in ``page_texts``.
    """

    def __init__(self, *, min_cells: int | None = None, merged_cells: bool = False):
        self.min_cells = min_cells
        self.merged_cells = merged_cells

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> RuledTables:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer

        grids: list[Grid] = []
        texts: list[str] = []
        page_texts: list[str] = []
        read_grid = merged_page_grid if self.merged_cells else page_grid
        for page in extract_pages(BytesIO(response.content)):
            page_text = [
                element.get_text()
                for element in page
                if isinstance(element, LTTextContainer)
            ]
            texts.extend(page_text)
            grid = read_grid(page)
            if grid is not None:
                grids.append(grid)
                if self.merged_cells:
                    page_texts.append("\n".join(page_text))
        text = "\n".join(texts)
        if self.min_cells is not None:
            filled = sum(1 for grid in grids for row in grid for cell in row if cell)
            response_shape.expect(
                filled >= self.min_cells,
                source_name=response_shape.source_name(source),
                detail=(
                    f"PDF holds {filled} ruled table cells, under {self.min_cells} "
                    "(image-only PDF or changed layout?)"
                ),
                raw=text[:500],
            )
        return RuledTables(text=text, grids=grids, page_texts=tuple(page_texts))
