import re
import urllib.parse
from datetime import date
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Stadt Gemünden (Wohra)"
DESCRIPTION = "Source for Stadt Gemünden (Wohra) waste collection schedule."
URL = "https://www.gemuenden-wohra.de"
COUNTRY = "de"

_SCHEDULE_URL = (
    "https://www.gemuenden-wohra.de/seite/461536/abfallentsorgung-abfuhrtermine.html"
)
_PDF_YEAR_RE = re.compile(r"Abfallkalender[_-]?(\d{4})\.pdf", re.IGNORECASE)
_WEEKDAY_RE = re.compile(r"(\d{2})\s+(Mo|Di|Mi|Do|Fr|Sa|So)")
_COLLECTION_RE = re.compile(r"([BRGP])\s+(1/2|[12])")
_AR_RE = re.compile(r"\bAR\b")
_SO_RE = re.compile(r"\bSO\b")

_CODE_MAP = {
    "B": "Bioabfall",
    "R": "Restmüll",
    "G": "Gelbe Tonne",
    "P": "Altpapier",
}

ICON_MAP = {
    "Bioabfall": Icons.ORGANIC,
    "Restmüll": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Altreifensammlung": Icons.GENERAL_WASTE,
    "Sonderabfall": Icons.HAZARDOUS,
}

TEST_CASES = {
    "Tour 1 (Schiffelbach, Ellnrode, Grüsen etc.)": {"tour": 1},
    "Tour 2 (Kernstadt Gemünden)": {"tour": 2},
}

PARAM_TRANSLATIONS = {
    "en": {"tour": "Collection tour"},
    "de": {"tour": "Abfuhrtour"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "tour": (
            "Tour 1: Schiffelbach, Ellnrode, Grüsen, Sehlen, Herbelhausen, "
            "Lehnhausen and areas west of the former railway line. "
            "Tour 2: Rest of Gemünden town centre."
        )
    },
    "de": {
        "tour": (
            "Tour 1: Schiffelbach, Ellnrode, Grüsen, Sehlen, Herbelhausen, "
            "Lehnhausen und alle Grundstücke westlich der ehemaligen Bahntrasse. "
            "Tour 2: Rest der Kernstadt Gemünden."
        )
    },
}


class Source:
    def __init__(self, tour: int) -> None:
        if tour not in (1, 2):
            raise SourceArgumentNotFoundWithSuggestions("tour", str(tour), ["1", "2"])
        self._tour = tour

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; HomeAssistant)"}
        )

        response = session.get(_SCHEDULE_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        current_year = date.today().year
        pdf_links: dict[int, str] = {}

        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            m = _PDF_YEAR_RE.search(href)
            if m:
                year = int(m.group(1))
                if year >= current_year:
                    pdf_links[year] = urllib.parse.urljoin(_SCHEDULE_URL, href)

        entries: list[Collection] = []
        for year, pdf_url in sorted(pdf_links.items()):
            pdf_response = session.get(pdf_url, timeout=30)
            pdf_response.raise_for_status()
            reader = PdfReader(BytesIO(pdf_response.content))
            layout_text = reader.pages[0].extract_text(extraction_mode="layout")
            entries.extend(self._parse_layout(layout_text, year))

        return entries

    def _parse_layout(self, text: str, year: int) -> list[Collection]:
        lines = text.split("\n")

        # Find the calendar header line (contains both "Januar" and "Februar")
        header_idx = next(
            (
                i
                for i, line in enumerate(lines)
                if "Januar" in line and "Februar" in line
            ),
            None,
        )
        if header_idx is None:
            return []

        # Determine column start positions from the first day line that has all
        # 12 months at evenly-spaced positions (holiday text can shift a column
        # on affected day lines, so we look for a clean reference line).
        col_boundaries: list[int] | None = None
        for line in lines[header_idx + 1 :]:
            matches = list(_WEEKDAY_RE.finditer(line))
            if len(matches) != 12:
                continue
            positions = [m.start() for m in matches]
            gaps = [positions[j + 1] - positions[j] for j in range(11)]
            if all(30 <= g <= 55 for g in gaps):
                col_boundaries = positions
                break

        if col_boundaries is None:
            return []

        col_ends = col_boundaries[1:] + [col_boundaries[-1] + 50]
        first_col_slice = slice(max(0, col_boundaries[0] - 5), col_boundaries[0] + 35)

        entries: list[Collection] = []
        for line in lines[header_idx + 1 :]:
            if not _WEEKDAY_RE.search(line):
                continue

            # Confirm the line starts with a day entry in the first month's column
            first_col_m = _WEEKDAY_RE.search(line[first_col_slice])
            if not first_col_m:
                continue
            day = int(first_col_m.group(1))

            for month_idx, (col_start, col_end) in enumerate(
                zip(col_boundaries, col_ends)
            ):
                if col_start >= len(line):
                    continue
                cell = line[col_start:col_end]
                month = month_idx + 1

                cell_m = _WEEKDAY_RE.search(cell)
                if not cell_m or int(cell_m.group(1)) != day:
                    continue

                try:
                    d = date(year, month, day)
                except ValueError:
                    continue

                for cm in _COLLECTION_RE.finditer(cell):
                    tour_group = cm.group(2)
                    if tour_group == "1/2" or int(tour_group) == self._tour:
                        waste_type = _CODE_MAP.get(cm.group(1), cm.group(1))
                        entries.append(
                            Collection(
                                date=d,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )

                # AR and SO events are not tour-specific
                if _AR_RE.search(cell):
                    entries.append(
                        Collection(
                            date=d,
                            t="Altreifensammlung",
                            icon=ICON_MAP.get("Altreifensammlung"),
                        )
                    )
                if _SO_RE.search(cell):
                    entries.append(
                        Collection(
                            date=d,
                            t="Sonderabfall",
                            icon=ICON_MAP.get("Sonderabfall"),
                        )
                    )

        return entries
