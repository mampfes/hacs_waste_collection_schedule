import io
import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTRect, LTTextLine
from waste_collection_schedule import Collection, Icons

TITLE = "Gemeinde Feuerthalen"
DESCRIPTION = (
    "Source for waste collection in Feuerthalen, Canton of Zurich, Switzerland."
)
URL = "https://www.feuerthalen.ch/umwelt/entsorgung/abfall.html/275"
COUNTRY = "ch"

SOURCE_CODEOWNERS = ["@oh-supra"]

TEST_CASES: dict[str, dict] = {
    "Feuerthalen": {},
}

_PRODUCT_URL = (
    "https://www.feuerthalen.ch/verwaltung/online-schalter.html/384/product/7"
)

ICON_MAP = {
    "Hauskehricht": Icons.GENERAL_WASTE,
    "Gruengut": Icons.ORGANIC,
    "Werkhof": Icons.RECYCLING,
    "AltpapierKarton": Icons.PAPER,
    "Sonderabfall": Icons.HAZARDOUS,
}

# Pretty labels for the internal (ASCII-safe) waste-type keys used while
# matching cell colours.
DISPLAY_NAME = {
    "Hauskehricht": "Hauskehricht",
    "Gruengut": "Grüngut",
    "Werkhof": "Direktentsorgung Werkhof",
    "AltpapierKarton": "Altpapier/Karton",
    "Sonderabfall": "Sonderabfälle/Giftsammlung",
}

MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]  # fmt: skip

WEEKDAYS_DE = {
    "Montag": 0,
    "Dienstag": 1,
    "Mittwoch": 2,
    "Donnerstag": 3,
    "Freitag": 4,
    "Samstag": 5,
    "Sonntag": 6,
}
_WEEKDAY_RE = "|".join(WEEKDAYS_DE)

# The calendar grid encodes each waste type as a small coloured square behind
# the day-of-month number; every municipality-wide (non-Hauskehricht) date is
# read off these colours. Hauskehricht itself has no colour (it is simply
# "every Monday", called out separately in the page-2 legend text together
# with its holiday-shift exceptions), so it is expanded programmatically.
_WASTE_COLORS: dict[tuple[float, float, float], str] = {
    (0.0, 0.483, 0.735): "Hauskehricht",
    (0.259, 0.606, 0.24): "Gruengut",
    (0.717, 0.65, 0.509): "Werkhof",
    (1.0, 0.795, 0.0): "AltpapierKarton",
    (0.896, 0.199, 0.532): "Sonderabfall",
}
_COLOR_TOL = 0.015


def _colors_close(c1: tuple | None, c2: tuple[float, float, float]) -> bool:
    if c1 is None or len(c1) != len(c2):
        return False
    return all(abs(a - b) < _COLOR_TOL for a, b in zip(c1, c2, strict=True))


def _walk(obj):
    yield obj
    if hasattr(obj, "__iter__"):
        for child in obj:
            yield from _walk(child)


def _extract_words(page) -> list[dict]:
    """Extract words with bounding boxes from a pdfminer page layout."""
    words: list[dict] = []
    for obj in _walk(page):
        if not isinstance(obj, LTTextLine):
            continue
        current: list[LTChar] = []
        for c in obj:
            if not isinstance(c, LTChar):
                continue
            if current and (
                c.x0 - current[-1].x1 > max(1.2, 0.35 * c.size)
                or not c.get_text().strip()
            ):
                _flush_word(words, current)
                current = []
            if c.get_text().strip():
                current.append(c)
        _flush_word(words, current)
    return words


def _flush_word(words: list[dict], chars: list) -> None:
    if not chars:
        return
    text = "".join(c.get_text() for c in chars).strip()
    if not text:
        return
    words.append(
        {
            "text": text,
            "x0": min(c.x0 for c in chars),
            "x1": max(c.x1 for c in chars),
            "y0": min(c.y0 for c in chars),
            "y1": max(c.y1 for c in chars),
        }
    )


def _find_year(words: list[dict]) -> int | None:
    text = " ".join(w["text"] for w in sorted(words, key=lambda w: -w["y0"]))
    m = re.search(r"ABFALLKALENDER\s+(\d{4})", text)
    return int(m.group(1)) if m else None


def _find_month_headers(words: list[dict]) -> list[dict]:
    return [w for w in words if w["text"] in MONTHS_DE]


def _nearest_month(rect: LTRect, month_headers: list[dict]) -> str | None:
    cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
    best, best_dist = None, None
    for h in month_headers:
        if h["y0"] < cy:  # a month header only ever sits above its own grid
            continue
        dist = (cx - h["x0"]) ** 2 + (cy - h["y0"]) ** 2
        if best_dist is None or dist < best_dist:
            best_dist, best = dist, h["text"]
    return best


def _day_number(rect: LTRect, words: list[dict]) -> int | None:
    cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
    for w in words:
        if (
            w["x0"] <= cx <= w["x1"]
            and w["y0"] <= cy <= w["y1"]
            and w["text"].isdigit()
        ):
            return int(w["text"])
    return None


def _parse_colored_grid(page, words: list[dict], year: int) -> set[tuple[str, date]]:
    month_headers = _find_month_headers(words)
    events: set[tuple[str, date]] = set()
    for rect in _walk(page):
        if not isinstance(rect, LTRect):
            continue
        waste_type = next(
            (
                name
                for color, name in _WASTE_COLORS.items()
                if name != "Hauskehricht"
                and _colors_close(rect.non_stroking_color, color)
            ),
            None,
        )
        if waste_type is None:
            continue
        month_name = _nearest_month(rect, month_headers)
        day = _day_number(rect, words)
        if month_name is None or day is None:
            continue
        try:
            events.add((waste_type, date(year, MONTHS_DE.index(month_name) + 1, day)))
        except ValueError:
            continue
    return events


def _expand_weekly_monday(year: int) -> set[date]:
    d = date(year, 1, 1)
    d += timedelta(days=(0 - d.weekday()) % 7)
    dates = set()
    while d.year == year:
        dates.add(d)
        d += timedelta(days=7)
    return dates


def _parse_hauskehricht_shifts(words: list[dict]) -> list[date]:
    """Parse holiday replacement dates, e.g. 'Mittwoch, 08.04.2026 statt Ostermontag'.

    Returns the collection dates that replace their week's Monday collection.
    """
    lines: dict[int, list[dict]] = {}
    for w in words:
        lines.setdefault(round(w["y0"]), []).append(w)
    text_lines = []
    for _, ws in sorted(lines.items(), key=lambda kv: -kv[0]):
        ws.sort(key=lambda w: w["x0"])
        text_lines.append(" ".join(w["text"] for w in ws))
    text = "\n".join(text_lines)

    shifts = []
    for m in re.finditer(
        rf"({_WEEKDAY_RE}),\s*(\d{{1,2}})\.(\d{{1,2}})\.(\d{{4}})\s+statt", text
    ):
        _weekday_name, day, month, year_str = m.groups()
        try:
            shifts.append(date(int(year_str), int(month), int(day)))
        except ValueError:
            continue
    return shifts


def _parse_hauskehricht(page2_words: list[dict], year: int) -> set[date]:
    mondays = _expand_weekly_monday(year)
    for shift_date in _parse_hauskehricht_shifts(page2_words):
        offset = shift_date.weekday()  # days after that week's Monday
        original_monday = shift_date - timedelta(days=offset)
        mondays.discard(original_monday)
        mondays.add(shift_date)
    return mondays


class Source:
    def __init__(self) -> None:
        # No parameters needed - Feuerthalen has common dates for the entire
        # municipality.
        pass

    def _find_pdf_url(self, session: requests.Session) -> str:
        r = session.get(_PRODUCT_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        link = soup.select_one('a[href*=".pdf"]')
        if link is None or not link.get("href"):
            raise ValueError(
                "No waste calendar PDF link found on the Feuerthalen online "
                "counter page. The website structure may have changed."
            )
        return str(link["href"])

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        pdf_url = self._find_pdf_url(session)
        r = session.get(pdf_url, timeout=30)
        r.raise_for_status()

        pages = list(extract_pages(io.BytesIO(r.content)))
        if not pages:
            raise ValueError("The waste calendar PDF has no pages.")

        page1_words = _extract_words(pages[0])
        year = _find_year(page1_words)
        if year is None:
            raise ValueError(
                "Could not determine the calendar year from the waste "
                "calendar PDF. The website structure may have changed."
            )

        grid_events = _parse_colored_grid(pages[0], page1_words, year)
        if not grid_events:
            raise ValueError(
                "No waste collection events found in the waste calendar PDF. "
                "The website structure may have changed."
            )

        page2_words = _extract_words(pages[1]) if len(pages) > 1 else []
        hauskehricht_dates = _parse_hauskehricht(page2_words, year)

        events: set[tuple[str, date]] = set(grid_events)
        events.update(("Hauskehricht", d) for d in hauskehricht_dates)

        return [
            Collection(
                date=collection_date,
                t=DISPLAY_NAME[waste_type],
                icon=ICON_MAP.get(waste_type),
            )
            for waste_type, collection_date in sorted(
                events, key=lambda e: (e[1], e[0])
            )
        ]
