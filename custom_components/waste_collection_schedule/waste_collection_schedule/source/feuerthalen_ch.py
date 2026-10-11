import re
from collections.abc import Iterable
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import parsers, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.transformers import ICSTransformer

_PRODUCT_URL = (
    "https://www.feuerthalen.ch/verwaltung/online-schalter.html/384/product/7"
)

HAUSKEHRICHT = "Hauskehricht"
GRUENGUT = "Grüngut"
WERKHOF = "Direktentsorgung Werkhof"
ALTPAPIER = "Altpapier/Karton"
SONDERABFALL = "Sonderabfälle/Giftsammlung"

MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]  # fmt: skip

_WEEKDAY_RE = "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag"

# The calendar grid encodes each waste type as a small coloured square behind
# the day-of-month number. Hauskehricht has no colour (it is "every Monday",
# called out in the legend text together with its holiday-shift exceptions),
# so it is expanded from the weekday rule.
_WASTE_COLORS: dict[tuple[float, float, float], str] = {
    (0.259, 0.606, 0.24): GRUENGUT,
    (0.717, 0.65, 0.509): WERKHOF,
    (1.0, 0.795, 0.0): ALTPAPIER,
    (0.896, 0.199, 0.532): SONDERABFALL,
}
_COLOR_TOL = 0.015
_MIN_CELL = 14.0


def _label_for_colour(color: tuple[float, ...] | None) -> str | None:
    if color is None or len(color) != 3:
        return None
    for known, label in _WASTE_COLORS.items():
        if all(abs(a - b) < _COLOR_TOL for a, b in zip(color, known, strict=True)):
            return label
    return None


def find_year(text: str) -> int | None:
    """The calendar year printed in the title ("ABFALLKALENDER 2026")."""
    m = re.search(r"ABFALLKALENDER\s+(\d{4})", text)
    return int(m.group(1)) if m else None


def weekly_mondays(year: int) -> set[date]:
    d = date(year, 1, 1)
    d += timedelta(days=(0 - d.weekday()) % 7)
    dates = set()
    while d.year == year:
        dates.add(d)
        d += timedelta(days=7)
    return dates


def holiday_shifts(text: str) -> list[date]:
    """Replacement dates, e.g. 'Mittwoch, 08.04.2026 statt Ostermontag'."""
    shifts = []
    for m in re.finditer(
        rf"(?:{_WEEKDAY_RE}),\s*(\d{{1,2}})\.(\d{{1,2}})\.(\d{{4}})\s+statt", text
    ):
        day, month, year = (int(g) for g in m.groups())
        try:
            shifts.append(date(year, month, day))
        except ValueError:
            continue
    return shifts


def _nearest_month(vec_cx: float, vec_cy: float, headers) -> str | None:
    best, best_dist = None, None
    for h in headers:
        if h.y < vec_cy:  # a month header only ever sits above its own grid
            continue
        dist = (vec_cx - h.x) ** 2 + (vec_cy - h.y) ** 2
        if best_dist is None or dist < best_dist:
            best_dist, best = dist, h.text
    return best


def _day_number(vec: parsers.PdfVector, words) -> int | None:
    cx, cy = (vec.x0 + vec.x1) / 2, (vec.y0 + vec.y1) / 2
    best, best_dist = None, None
    for w in words:
        if w.page != vec.page or not w.text.isdigit():
            continue
        if not (vec.x0 <= w.x <= vec.x1 and vec.y0 <= w.y <= vec.y1):
            continue
        dist = (w.x - cx) ** 2 + (w.y - cy) ** 2
        if best_dist is None or dist < best_dist:
            best, best_dist = int(w.text), dist
    return best


def collection_rows(
    layouts: list[parsers.PdfWordLayout], source: BaseSource
) -> Iterable[tuple[date, str]]:
    (layout,) = layouts
    name = response_shape.source_name(source)
    first_page = [w for w in layout.words if w.page == 0]
    year = find_year(" ".join(line.text for line in layout.lines if line.page == 0))
    response_shape.expect(
        year is not None,
        source_name=name,
        detail="could not determine the calendar year from the PDF",
        raw=str(layout.lines[:10]),
    )
    assert year is not None

    headers = [w for w in first_page if w.text in MONTHS_DE]
    events: set[tuple[date, str]] = set()
    for vec in layout.vectors:
        if vec.page != 0:
            continue
        label = _label_for_colour(vec.fill_color)
        # Day cells are 15x15 squares; the smaller 13x13 shapes in the same
        # colour mark the weekly Monday round and are not collection days.
        if label is None or min(vec.x1 - vec.x0, vec.y1 - vec.y0) < _MIN_CELL:
            continue
        month = _nearest_month((vec.x0 + vec.x1) / 2, (vec.y0 + vec.y1) / 2, headers)
        day = _day_number(vec, first_page)
        if month is None or day is None:
            continue
        try:
            events.add((date(year, MONTHS_DE.index(month) + 1, day), label))
        except ValueError:
            continue
    response_shape.expect(
        bool(events),
        source_name=name,
        detail="no coloured collection days found in the calendar grid",
        raw=str(layout.lines[:10]),
    )

    # The exception notes live on page 2 today; scan every later page so a
    # future re-layout does not silently drop them.
    note_text = "\n".join(line.text for line in layout.lines if line.page > 0)
    mondays = weekly_mondays(year)
    for shifted in holiday_shifts(note_text):
        mondays.discard(shifted - timedelta(days=shifted.weekday()))
        mondays.add(shifted)
    events.update((d, HAUSKEHRICHT) for d in mondays)
    yield from sorted(events)


@final
class Source(BaseSource):
    TITLE = "Gemeinde Feuerthalen"
    DESCRIPTION = (
        "Source for waste collection in Feuerthalen, Canton of Zurich, Switzerland."
    )
    URL = "https://www.feuerthalen.ch/umwelt/entsorgung/abfall.html/275"
    COUNTRY = "ch"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@oh-supra"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {"Feuerthalen": {}}

    PARAMS = ()

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "No configuration needed: Feuerthalen publishes one waste calendar for the whole municipality.",
        "de": "Keine Angaben nötig: Feuerthalen veröffentlicht einen Abfallkalender für die ganze Gemeinde.",
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_PRODUCT_URL, pattern=r"\.pdf", select="first"
    )
    parse = parsers.PdfWordLayoutParser(min_words=50, min_vectors=1)
    preprocess = staticmethod(collection_rows)
    transform = ICSTransformer(
        type_value_map={
            HAUSKEHRICHT: wt.GENERAL_WASTE,
            GRUENGUT: wt.GARDEN_WASTE,
            WERKHOF: wt.RECYCLABLES,
            ALTPAPIER: wt.PAPER,
            SONDERABFALL: wt.HAZARDOUS,
        }
    )
