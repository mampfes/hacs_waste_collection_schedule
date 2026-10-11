"""Pipeline components for the KOSIT (Košice, SK) municipal collection calendars.

KOSIT EAST (kositeast.sk) and KOSIT WEST (kositwest.sk) each publish one
single-page PDF per municipality, linked by the municipality's name from a
stable index page. The PDF is a year planner: the days of a month are printed
as text ("Po 5") and the days a waste type is collected are marked by a small
filled rectangle in that waste type's colour. The two operators share the
layout and differ only in the month grid (6 columns by 2 rows for EAST, 3 by 4
for WEST), the rectangle size, the shade of two of the colours and where the
year is printed.

:func:`pdf_link` is the ``pick`` of the index :class:`~retrievers.Lookup` (it
finds the municipality's PDF by link text), and :class:`CalendarParser` decodes
the PDF into ``(date, label)`` records that the source's ``ICSTransformer``
maps to waste types. The grid is inferred from the rectangle positions, so it
adapts to a re-generated PDF; a missing year or an unrecognised colour fails
loudly instead of returning a wrong schedule.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from io import BytesIO
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

#: Labels emitted for the colour-coded rectangles (the Slovak names).
GENERAL = "Komunálny odpad"
PLASTICS = "Plasty, VKM, Kovové obaly"
GLASS = "Sklo"
PAPER = "Papier"
OIL = "Jedlé oleje a tuky"
HAZARDOUS = "Nebezpečný odpad"

#: RGB fills (rounded to 3 d.p.) shared by both operators.
COLOURS: dict[tuple[float, ...], str] = {
    (1.0, 1.0, 0.0): PLASTICS,
    (0.451, 0.89, 0.008): GLASS,
    (0.584, 0.729, 1.0): PAPER,
    (1.0, 0.702, 0.4): OIL,
    (0.741, 0.494, 0.984): HAZARDOUS,
    (0.0, 0.0, 0.0): GENERAL,
}

#: Maximum Euclidean RGB distance accepted as a colour match (the nearest
#: neighbours in the palette are all more than 0.3 apart).
COLOUR_TOLERANCE = 0.05

_DAY_RE = re.compile(r"(?:^|[^\W\d_]+\s+)(\d+)\b")


def pdf_link(response: Any, *_keys: Any, town: str, **_params: Any) -> str:
    """The PDF linked from the index page under the municipality's name."""
    soup = BeautifulSoup(response.text, "html.parser")
    wanted = str(town).strip().casefold()
    known: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        if not href.lower().endswith(".pdf"):
            continue
        name = anchor.get_text(strip=True)
        known.append(name)
        if name.casefold() == wanted:
            return urljoin(str(response.url), href)
    raise SourceArgumentNotFoundWithSuggestions("town", town, sorted(set(known)))


class _Rect(NamedTuple):
    bbox: tuple[float, float, float, float]
    colour: tuple[float, ...]


def _cluster(values: Sequence[float], n: int) -> list[float]:
    """Cluster ``values`` into at most ``n`` groups; sorted centre positions.

    Values are rounded and deduplicated, adjacent ones less than 5 pt apart are
    merged, then the closest adjacent pair is merged until ``n`` groups remain.
    """
    merged: list[float] = []
    for v in sorted({round(v, 1) for v in values}):
        if merged and v - merged[-1] < 5.0:
            merged[-1] = (merged[-1] + v) / 2
        else:
            merged.append(v)
    while len(merged) > n:
        gaps = [merged[i + 1] - merged[i] for i in range(len(merged) - 1)]
        idx = gaps.index(min(gaps))
        merged[idx] = (merged[idx] + merged[idx + 1]) / 2
        del merged[idx + 1]
    return merged


def _nearest(value: float, centres: Sequence[float]) -> int:
    return min(range(len(centres)), key=lambda i: abs(centres[i] - value))


class CalendarParser(Parser["list[tuple[date, str]]"]):
    """Decode a KOSIT year-planner PDF into ``(date, label)`` records.

    Args:
        columns, rows: the month grid of one page (months run left to right,
            top to bottom).
        max_rect_width: widest marker, as a fraction of the page width.
        match_horizontal_overlap: pair a marker with the day text it overlaps
            horizontally (WEST); otherwise with the day text in the same grid
            column (EAST).
        colours: fill colour to label; ``extra_colours`` adds shades.
        ignored: fills that are page decoration, not markers.
        year_pattern: regex whose first group is the schedule year.
    """

    def __init__(
        self,
        *,
        columns: int,
        rows: int,
        max_rect_width: float,
        match_horizontal_overlap: bool,
        year_pattern: str,
        extra_colours: Mapping[tuple[float, ...], str] | None = None,
        ignored: Sequence[tuple[float, ...]] = (),
    ):
        self.columns = columns
        self.rows = rows
        self.max_rect_width = max_rect_width
        self.match_horizontal_overlap = match_horizontal_overlap
        self.year_pattern = re.compile(year_pattern, re.IGNORECASE)
        self.colours = {**COLOURS, **(extra_colours or {})}
        self.ignored = set(ignored)

    def _label(self, colour: tuple[float, ...]) -> str | None:
        best, best_dist = None, float("inf")
        for known, name in self.colours.items():
            if len(known) != len(colour):
                continue
            dist = sum((a - b) ** 2 for a, b in zip(colour, known, strict=True)) ** 0.5
            if dist < best_dist:
                best, best_dist = name, dist
        return best if best_dist <= COLOUR_TOLERANCE else None

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTRect, LTTextContainer, LTTextLine

        name = response_shape.source_name(source)
        pages = list(extract_pages(BytesIO(response.content)))
        response_shape.expect(
            bool(pages), source_name=name, detail="the PDF has no pages"
        )

        def text_lines(page):
            for element in page:
                if isinstance(element, LTTextContainer):
                    for line in element:
                        if isinstance(line, LTTextLine):
                            text = line.get_text().strip()
                            if text:
                                yield line.bbox, text

        year: int | None = None
        for page in pages:
            for _bbox, text in text_lines(page):
                if match := self.year_pattern.search(text):
                    year = int(match.group(1))
                    break
            if year is not None:
                break
        response_shape.expect(
            year is not None,
            source_name=name,
            detail="could not determine the schedule year; the PDF layout changed",
        )
        assert year is not None

        records: list[tuple[date, str]] = []
        for page in pages:
            records.extend(self._page(page, year, text_lines(page), LTRect, name))
        return sorted(set(records))

    def _page(self, page, year, lines_iter, rect_type, name) -> list[tuple[date, str]]:
        page_w, page_h = page.bbox[2], page.bbox[3]
        min_w, max_w = page_w * 0.011, page_w * self.max_rect_width
        min_h, max_h = page_h * 0.005, page_h * 0.016

        lines = list(lines_iter)
        rects: list[_Rect] = []
        for element in page:
            if not isinstance(element, rect_type):
                continue
            if not (min_w < element.width < max_w and min_h < element.height < max_h):
                continue
            colour = element.non_stroking_color
            if isinstance(colour, (int, float)):
                colour = (round(colour, 3),) * 3
            elif colour is not None:
                colour = tuple(round(c, 3) for c in colour)
            else:
                colour = (0.0, 0.0, 0.0)
            if colour not in self.ignored:
                rects.append(_Rect(element.bbox, colour))
        if not rects:
            _LOGGER.warning("No schedule rectangles found on a page of %s", name)
            return []

        x_clusters = _cluster(
            [(r.bbox[0] + r.bbox[2]) / 2 for r in rects], self.columns
        )
        y_clusters = _cluster([(r.bbox[1] + r.bbox[3]) / 2 for r in rects], self.rows)
        if len(x_clusters) != self.columns or len(y_clusters) != self.rows:
            _LOGGER.warning(
                "Expected a %dx%d month grid in %s, found %dx%d; month "
                "assignments may be wrong.",
                self.columns,
                self.rows,
                name,
                len(x_clusters),
                len(y_clusters),
            )

        out: list[tuple[date, str]] = []
        for rect in rects:
            rx0, ry0, rx1, ry1 = rect.bbox
            col = _nearest((rx0 + rx1) / 2, x_clusters)
            row = _nearest((ry0 + ry1) / 2, y_clusters)
            # pdfminer's y axis points up, so the last cluster is the top row
            month = (self.rows - 1 - row) * self.columns + col + 1

            day = None
            for (lx0, ly0, lx1, ly1), text in lines:
                if max(ry0, ly0) >= min(ry1, ly1):
                    continue
                if self.match_horizontal_overlap:
                    if max(rx0, lx0) >= min(rx1, lx1):
                        continue
                elif _nearest((lx0 + lx1) / 2, x_clusters) != col:
                    continue
                if found := _DAY_RE.search(text):
                    day = int(found.group(1))
                    break
            if day is None:
                continue

            label = self._label(rect.colour)
            if label is None:
                _LOGGER.warning("Unrecognised colour %s in %s", rect.colour, name)
                continue
            try:
                out.append((date(year, month, day), label))
            except ValueError:
                _LOGGER.warning("Invalid date %s-%s-%s in %s", year, month, day, name)
        return out
