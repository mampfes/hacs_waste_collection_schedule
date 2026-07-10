import io
import re
from calendar import monthcalendar
from datetime import date, datetime

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Kópavogsbær"
DESCRIPTION = "Source for Kópavogur, Iceland (Kubbur collection calendar)"
URL = "https://www.kopavogur.is"
COUNTRY = "is"
SOURCE_CODEOWNERS = ["@rhubarbgarden"]

DISTRICTS = [
    "Vesturbær - Smárahverfi",
    "Austurbær sunnan Álfhólsvegar",
    "Austurbær norðan Álfhólsvegar",
    "Lindir, Salir, Kórar, Hvörf og Þing",
]

# Highlight fill colors used in the PDF calendars, mapped to district index
_DISTRICT_COLORS = {
    (1.0, 1.0, 0.0): 0,  # yellow
    (0.8, 0.4, 1.0): 1,  # purple
    (1.0, 0.0, 0.0): 2,  # red
    (0.0, 0.69, 0.941): 3,  # blue
}
_GRAY = 0.949  # fill of the weekday header bar above each mini calendar

PDF_URLS = {
    "Almennt sorp og matarleifar": "https://eldri.kopavogur.is/static/files/Sorphirda/sorphirdudagatal-{year}-almennt.pdf",
    "Pappi/pappír og plast": "https://eldri.kopavogur.is/static/files/Sorphirda/sorphirdudagatal-{year}-pappi-plast.pdf",
}

ICON_MAP = {
    "Almennt sorp og matarleifar": Icons.GENERAL_WASTE,
    "Pappi/pappír og plast": Icons.RECYCLING,
}

TEST_CASES = {
    "Vesturbær": {"district": "Vesturbær - Smárahverfi"},
    "Austurbær sunnan": {"district": "Austurbær sunnan Álfhólsvegar"},
    "Austurbær norðan": {"district": "Austurbær norðan Álfhólsvegar"},
    "Lindir": {"district": "Lindir, Salir, Kórar, Hvörf og Þing"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "district": "District",
    },
    "de": {
        "district": "Bezirk",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "district": "Collection district (zone) as shown in the calendar legend. Partial, case-insensitive matches are accepted.",
    },
    "de": {
        "district": "Abfuhrbezirk (Zone) wie in der Kalenderlegende angegeben. Teilweise Übereinstimmungen (Groß-/Kleinschreibung wird ignoriert) werden akzeptiert.",
    },
}

# content stream operators: "r g b rg" (set rgb fill), "v g" (set gray fill),
# "x y w h re" followed by "f*" (fill rectangle)
_STREAM_RE = re.compile(
    r"(?:([\d.]+) ([\d.]+) ([\d.]+) rg)"
    r"|(?:([\d.]+) g\b)"
    r"|(?:([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) re\s+f\*)"
)


def _extract_rects(stream: str):
    """Yield (district_index_or_"gray", x, y, w) for filled rects of interest."""
    color = None
    for m in _STREAM_RE.finditer(stream):
        if m.group(1) is not None:  # rgb fill color
            color = tuple(round(float(m.group(i)), 3) for i in (1, 2, 3))
        elif m.group(4) is not None:  # gray fill color
            color = ("gray", round(float(m.group(4)), 3))
        else:  # filled rectangle
            x, y, w, _h = (float(m.group(i)) for i in range(5, 9))
            if color == ("gray", _GRAY):
                yield "gray", x, y, w
            elif color in _DISTRICT_COLORS:
                yield _DISTRICT_COLORS[color], x, y, w


class Source:
    def __init__(self, district: str | None = None):
        if not district:
            raise SourceArgumentRequired(
                "district", "district (collection zone) is required"
            )
        normalized = district.strip().casefold()
        matches = [d for d in DISTRICTS if normalized in d.casefold()]
        if len(matches) != 1:
            raise SourceArgumentNotFoundWithSuggestions("district", district, DISTRICTS)
        self._district_index = DISTRICTS.index(matches[0])

    def fetch(self) -> list[Collection]:
        year = datetime.now().year
        entries = self._fetch_year(year)
        # Early in the year, last year's calendar may still contain
        # upcoming dates (and the new PDF may not exist yet).
        if not entries or datetime.now().month == 1:
            try:
                entries += [
                    e for e in self._fetch_year(year - 1) if e.date >= date.today()
                ]
            except Exception:
                pass
        if not entries:
            raise Exception("no collection dates found in calendar PDFs")
        return entries

    def _fetch_year(self, year: int) -> list[Collection]:
        entries: list[Collection] = []
        for waste_type, url_template in PDF_URLS.items():
            r = requests.get(url_template.format(year=year), timeout=30)
            r.raise_for_status()
            for d in self._parse_pdf(r.content, year):
                entries.append(
                    Collection(date=d, t=waste_type, icon=ICON_MAP.get(waste_type))
                )
        return entries

    def _parse_pdf(self, pdf_bytes: bytes, year: int) -> list[date]:
        page = PdfReader(io.BytesIO(pdf_bytes)).pages[0]
        stream = page.get_contents().get_data().decode("latin-1")

        weekday_bars = []  # gray bar above each mini calendar: (x, y, w)
        all_highlights = []  # (district_index, x, y, w)
        for kind, x, y, w in _extract_rects(stream):
            if kind == "gray":
                weekday_bars.append((x, y, w))
            else:
                all_highlights.append((kind, x, y, w))

        if len(weekday_bars) != 12:
            raise Exception(
                f"unexpected calendar layout: {len(weekday_bars)} month grids"
            )

        # month grid geometry: 4 columns x 3 bands, anchored on weekday bars
        col_xs = sorted({round(b[0], 2) for b in weekday_bars})
        band_ys = sorted({round(b[1], 2) for b in weekday_bars}, reverse=True)
        if len(col_xs) != 4 or len(band_ys) != 3:
            raise Exception("unexpected calendar layout: month grid mismatch")
        cell_w = weekday_bars[0][2] / 7
        # legend boxes at the bottom are wider than any highlight; drop them
        all_highlights = [h for h in all_highlights if h[3] < 3 * cell_w]
        # vertical row pitch: smallest gap between any highlight and its bar
        pitch = min(
            min(b - y for b in band_ys if b > y) for _i, _x, y, _w in all_highlights
        )

        dates: list[date] = []
        for dist, x, y, w in all_highlights:
            if dist != self._district_index:
                continue
            col = max(i for i in range(4) if col_xs[i] - 2 <= x)
            band_y = min((b for b in band_ys if b > y), key=lambda b: b - y)
            month = band_ys.index(band_y) * 4 + col + 1
            weekday0 = round((x - col_xs[col]) / cell_w)
            week0 = round((band_y - y) / pitch) - 1
            weeks = monthcalendar(year, month)
            for k in range(round(w / cell_w)):  # a wide rect spans 2 days
                weekday = (weekday0 + k) % 7
                week = week0 + (weekday0 + k) // 7
                day = weeks[week][weekday] if 0 <= week < len(weeks) else 0
                if day == 0:
                    raise Exception(f"failed to decode calendar cell in month {month}")
                d = date(year, month, day)
                if d.weekday() != weekday:  # geometric sanity check
                    raise Exception("calendar grid decoding mismatch")
                dates.append(d)
        return dates
