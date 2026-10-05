"""Pipeline components for the Kopavogur (IS) collection calendar PDFs.

Kopavogur publishes one single-page PDF per round and year: twelve mini month
grids, each day printed as a text fragment, and the days a district is served
highlighted with a filled rectangle in that district's colour (a rectangle two
cells wide marks two consecutive days). The colour-to-district mapping is
printed in a legend at the foot of the page.

:class:`CalendarParser` reads such a PDF and emits ``(date, label)`` records for
the configured district. The year is not printed on the page; it is part of the
PDF's file name (``sorphirdudagatal-2026-almennt...``), which is also what names
the round, so both come from the response URL. Every decoded cell is checked
against the calendar (the day must exist in that month and fall on the weekday
column the rectangle sits in) so a changed layout fails loudly.

The label is a plain string; the source's transformer maps it to a canonical
``WasteType``.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser, PdfLayoutParser, PdfVector

if TYPE_CHECKING:
    from collections.abc import Mapping

    from waste_collection_schedule.base_source import BaseSource

#: The collection districts, in the order of the highlight colours below.
DISTRICTS = (
    "Vesturbær - Smárahverfi",
    "Austurbær sunnan Álfhólsvegar",
    "Austurbær norðan Álfhólsvegar",
    "Lindir, Salir, Kórar, Hvörf og Þing",
)

# Highlight fill colours used in the calendars, one per district.
_DISTRICT_COLOURS = (
    (1.0, 1.0, 0.0),  # yellow
    (0.8, 0.4, 1.0),  # purple
    (1.0, 0.0, 0.0),  # red
    (0.0, 0.69, 0.941),  # blue
)
_BAR_GRAY = 0.949  # fill of the weekday header bar above each mini calendar
_COLOUR_TOLERANCE = 0.01

#: Round names as they appear in the PDF file name, and the label emitted.
ROUNDS = {
    "almennt": "Almennt sorp og matarleifar",
    "pappi-plast": "Pappi/pappír og plast",
}

_URL_RE = re.compile(
    r"sorphirdudagatal-(\d{4})-([a-z-]+?)(?:-\d+)?\.pdf", re.IGNORECASE
)
_DAY_RE = re.compile(r"^\d{1,2}$")


def resolve_district(value: Any) -> int:
    """Index of the district named by ``value`` (a unique, partial match is fine)."""
    if not value or not str(value).strip():
        raise SourceArgumentRequired(
            "district", "district (collection zone) is required"
        )
    wanted = str(value).strip().casefold()
    matches = [i for i, name in enumerate(DISTRICTS) if wanted in name.casefold()]
    if len(matches) != 1:
        raise SourceArgumentNotFoundWithSuggestions("district", value, list(DISTRICTS))
    return matches[0]


def _is_fill(vector: PdfVector, colour: tuple[float, ...]) -> bool:
    fill = vector.fill_color
    return (
        fill is not None
        and len(fill) == len(colour)
        and all(
            abs(a - b) <= _COLOUR_TOLERANCE for a, b in zip(fill, colour, strict=True)
        )
    )


class CalendarParser(Parser["list[tuple[date, str]]"]):
    """Decode the configured district's dates from one calendar PDF.

    Takes the PDF response (the round and year are read from its URL) and
    returns ``(date, label)`` records, ``label`` being the round's name from
    :data:`ROUNDS`. The district is read from the source's ``district`` param.
    """

    def __init__(self, *, argument: str = "district"):
        self.argument = argument

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        params: Mapping[str, Any] = source.params if source is not None else {}
        district = resolve_district(params.get(self.argument))
        name = response_shape.source_name(source)

        match = _URL_RE.search(str(getattr(response, "url", "")))
        response_shape.expect(
            match is not None and match.group(2).lower() in ROUNDS,
            source_name=name,
            detail=f"cannot tell the round and year from the PDF URL {response.url}",
        )
        assert match is not None
        year = int(match.group(1))
        label = ROUNDS[match.group(2).lower()]

        layout = PdfLayoutParser(min_fragments=50, min_vectors=50)(response, source)

        bars = [v for v in layout.vectors if _is_fill(v, (_BAR_GRAY,))]
        response_shape.expect(
            len(bars) == 12,
            source_name=name,
            detail=f"unexpected calendar layout: {len(bars)} month grids",
        )
        col_xs = sorted({round(b.x0, 1) for b in bars})
        band_ys = sorted({round(b.y0, 1) for b in bars}, reverse=True)
        response_shape.expect(
            len(col_xs) == 4 and len(band_ys) == 3,
            source_name=name,
            detail="unexpected calendar layout: month grid mismatch",
        )
        cell_w = (bars[0].x1 - bars[0].x0) / 7

        days = [f for f in layout.fragments if _DAY_RE.match(f.text)]
        dates: list[date] = []
        for vector in layout.vectors:
            # the legend boxes at the foot are wider than any highlight
            if not _is_fill(vector, _DISTRICT_COLOURS[district]):
                continue
            width = vector.x1 - vector.x0
            if width >= 3 * cell_w:
                continue
            col = max(i for i in range(4) if col_xs[i] - 2 <= vector.x0)
            band_y = min(
                (b for b in band_ys if b > vector.y0), key=lambda b: b - vector.y0
            )
            month = band_ys.index(band_y) * 4 + col + 1
            weekday0 = round((vector.x0 - col_xs[col]) / cell_w)
            cells = sorted(
                (
                    f
                    for f in days
                    if f.page == vector.page
                    and vector.x0 - 1 <= f.x < vector.x1
                    and vector.y0 - 2 <= f.y <= vector.y1
                ),
                key=lambda f: f.x,
            )
            response_shape.expect(
                len(cells) == round(width / cell_w),
                source_name=name,
                detail=f"failed to decode calendar cell in month {month}",
            )
            for k, cell in enumerate(cells):
                try:
                    day = date(year, month, int(cell.text))
                except ValueError:
                    day = None
                response_shape.expect(
                    day is not None and day.weekday() == (weekday0 + k) % 7,
                    source_name=name,
                    detail="calendar grid decoding mismatch",
                )
                assert day is not None
                dates.append(day)
        return [(d, label) for d in sorted(set(dates))]
