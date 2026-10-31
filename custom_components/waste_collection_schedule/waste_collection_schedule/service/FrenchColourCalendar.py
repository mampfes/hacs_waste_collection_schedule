"""Dated French PDF calendars with colour-coded collection areas.

Read the printed month grids and area legends, including holiday replacements.
Never project dates beyond the published documents.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from collections import Counter
from datetime import date, timedelta

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import PdfTextFragment, PdfVector, PdfWordLayout
from waste_collection_schedule.response_shape import expect

_MONTHS = dict(
    zip(
        "janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre".split(),
        range(1, 13),
        strict=True,
    )
)
_DAYS = "lundi mardi mercredi jeudi vendredi samedi dimanche".split()
_SHORT_DAYS = "lu ma me je ve sa di".split()
GRAND_LIEU_COMMUNES = [
    "Le Bignon",
    "Geneston",
    "La Limouzinière",
    "Montbert",
    "Saint Colomban",
    "Saint Lumine de Coutais",
]


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _check(condition: bool, detail: str) -> None:
    expect(condition, source_name="French colour calendar", detail=detail, raw="")


def _close(a: tuple[float, ...] | None, b: tuple[float, ...] | None) -> bool:
    return bool(
        a
        and b
        and len(a) == len(b)
        and max(abs(x - y) for x, y in zip(a, b, strict=True)) < 0.025
    )


def _contains(v: PdfVector, p: PdfTextFragment) -> bool:
    if not (v.page == p.page and v.x0 <= p.x <= v.x1 and v.y0 <= p.y <= v.y1):
        return False
    points = getattr(v, "points", ())
    if not points:
        return True
    inside = False
    for (x1, y1), (x2, y2) in zip(points, (*points[1:], points[0]), strict=True):
        if (y1 > p.y) != (y2 > p.y) and p.x < (x2 - x1) * (p.y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _background(layout: PdfWordLayout, p: PdfTextFragment, colours=None):
    candidates = [
        v
        for v in layout.vectors
        if v.fill_color
        and _contains(v, p)
        and (colours is None or any(_close(v.fill_color, c) for c in colours))
    ]
    candidates.sort(key=lambda v: (v.x1 - v.x0) * (v.y1 - v.y0))
    return candidates[0].fill_color if candidates else None


def _headers(layout: PdfWordLayout):
    headers = [
        p for p in layout.words if p.text.isupper() and _normalise(p.text) in _MONTHS
    ]
    pages = [page for page, n in Counter(p.page for p in headers).items() if n == 12]
    _check(len(pages) == 1, "expected one complete twelve-month calendar grid")
    return [p for p in headers if p.page == pages[0]]


def _year(layout: PdfWordLayout) -> int:
    years = {int(p.text) for p in layout.lines if re.fullmatch(r"20\d\d", p.text)}
    _check(len(years) == 1, "calendar has no unambiguous printed year")
    return years.pop()


def _grid_cells(layout: PdfWordLayout, headers: list[PdfTextFragment], year: int):
    """Read mini-months and verify every date against its weekday column."""
    cells = {}
    for header in headers:
        month = _MONTHS[_normalise(header.text)]
        neighbours = [
            abs(p.x - header.x)
            for p in headers
            if abs(p.y - header.y) < 5 and p != header
        ]
        width = min(neighbours)
        columns = {
            _SHORT_DAYS.index(_normalise(p.text)): p.x
            for p in layout.words
            if p.page == header.page
            and 0 < header.y - p.y < 20
            and abs(p.x - header.x) < width / 2
            and _normalise(p.text) in _SHORT_DAYS
        }
        _check(len(columns) == 7, f"month {month}: missing weekday headers")
        next_y = max(
            (p.y for p in headers if p.y < header.y - 5), default=header.y - 150
        )
        for p in layout.words:
            if p.page != header.page or not re.fullmatch(r"\d{1,2}", p.text):
                continue
            if not (next_y + 10 < p.y < header.y - 20):
                continue
            day = int(p.text)
            if not 1 <= day <= calendar.monthrange(year, month)[1]:
                continue
            d = date(year, month, day)
            if abs(p.x - columns[d.weekday()]) < 4:
                _check(d not in cells, f"duplicate calendar date {d}")
                cells[d] = p
        expected = {
            date(year, month, d)
            for d in range(1, calendar.monthrange(year, month)[1] + 1)
        }
        _check(
            expected <= cells.keys(),
            f"month {month}: missing dates or weekday columns changed",
        )
    return cells


def syvalorm_rows(documents, source=None):
    """Resolve an area's printed map colour separately for every calendar year."""
    wanted = _normalise(source.params["municipality"])
    rows = []
    for layout in documents:
        headers = _headers(layout)
        cells = _grid_cells(layout, headers, _year(layout))
        colours = {
            c
            for p in cells.values()
            if (c := _background(layout, p)) and len(c) == 4 and max(c[:3]) > 0.1
        }
        _check(len(colours) >= 8, "calendar collection colours changed")
        # The map names every commune. A second legend on the calendar page
        # lists changed rounds and takes precedence over the map.
        matches = [p for p in layout.lines if _normalise(p.text) == wanted]
        selected = []
        for p in matches:
            swatches = [
                v
                for v in layout.vectors
                if v.page == p.page
                and p.page == headers[0].page
                and v.y0 <= p.y <= v.y1
                and 0 < p.x - v.x1 < 50
                and 5 < v.x1 - v.x0 < 25
                and any(_close(v.fill_color, c) for c in colours)
            ]
            if swatches:
                selected.append(min(swatches, key=lambda v: p.x - v.x1).fill_color)
            elif colour := _background(layout, p, colours):
                selected.append(colour)
        if not selected:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                source.params["municipality"],
                sorted(
                    {p.text for p in layout.lines if _background(layout, p, colours)}
                ),
            )
        colour = selected[-1]
        days = sorted(
            d for d, p in cells.items() if _close(_background(layout, p), colour)
        )
        _check(
            24 <= len(days) <= 28,
            "expected a fortnightly collection calendar for the selected area",
        )
        rows.extend((d, label) for d in days for label in ("general", "recycling"))
    return sorted(set(rows))


def grand_lieu_rows(documents, source=None):
    """Read the six-commune week colours and the PDF's holiday-to-Saturday rule."""
    wanted = _normalise(source.params["municipality"])
    valid = {_normalise(name): name for name in GRAND_LIEU_COMMUNES}
    if wanted not in valid:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", source.params["municipality"], GRAND_LIEU_COMMUNES
        )
    rows = []
    for layout in documents:
        headers = _headers(layout)
        page = headers[0].page
        year = _year(layout)
        legend_name = "saint lumine" if wanted == "saint lumine de coutais" else wanted
        names = [
            p
            for p in layout.lines
            if p.page == page and _normalise(p.text) == legend_name
        ]
        _check(len(names) == 1, "municipality missing from calendar legend")
        name = names[0]
        weekdays = [
            p
            for p in layout.words
            if p.page == page and _normalise(p.text) in _DAYS and abs(p.y - name.y) < 8
        ]
        _check(len(weekdays) == 1, "municipality collection weekday missing")
        weekday = weekdays[0]
        colour = _background(layout, weekday)
        _check(colour is not None, "municipality week colour missing")
        # Month headers and day numbers are positioned in twelve vertical
        # columns. Build bands at their midpoints, including split text runs.
        headers = sorted(headers, key=lambda p: p.x)
        cells = {}
        for i, header in enumerate(headers):
            left = (headers[i - 1].x + header.x) / 2 if i else header.x - 30
            right = (header.x + headers[i + 1].x) / 2 if i < 11 else header.x + 30
            month = _MONTHS[_normalise(header.text)]
            lines = [
                p
                for p in layout.lines
                if p.page == page and left <= p.x < right and p.y < header.y
            ]
            for p in lines:
                m = re.fullmatch(r"([LMMJVSD])\s*(\d{1,2})", p.text)
                if not m:
                    continue
                d = date(year, month, int(m[2]))
                _check(m[1] == "LMMJVSD"[d.weekday()], f"weekday mismatch for {d}")
                _check(d not in cells, f"duplicate date {d}")
                cells[d] = (p, [x.text for x in lines if abs(x.y - p.y) < 3])
            _check(
                sum(d.month == month for d in cells)
                == calendar.monthrange(year, month)[1],
                f"month {month}: incomplete day grid",
            )
        matching = [
            d for d, (p, _) in cells.items() if _close(_background(layout, p), colour)
        ]
        parities = {d.isocalendar().week % 2 for d in matching}
        _check(
            len(parities) == 1 and len(matching) > 100,
            "calendar week colour is inconsistent",
        )
        parity = parities.pop()
        text = _normalise(" ".join(p.text for p in layout.lines))
        _check(
            "samedi suivant" in text and "jours feries" in text,
            "holiday replacement rule changed",
        )
        for d, (_, labels) in cells.items():
            if (
                d.weekday() != _DAYS.index(_normalise(weekday.text))
                or d.isocalendar().week % 2 != parity
            ):
                continue
            if any(_normalise(label) == "ferie" for label in labels):
                d += timedelta(days=(5 - d.weekday()) % 7)
            rows.extend((d, label) for label in ("general", "recycling"))
    return sorted(set(rows))
