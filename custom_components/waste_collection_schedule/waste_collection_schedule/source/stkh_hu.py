"""Source for STKH Sopron és Térsége Nonprofit Kft., Hungary."""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "STKH Sopron és Térsége Nonprofit Kft."
DESCRIPTION = "Source script for stkh.hu"
URL = "https://stkh.hu"
COUNTRY = "hu"

TEST_CASES = {
    "Újkér": {"municipality": "Újkér"},
    "Fertőd": {"municipality": "Fertőd"},
    "Zsira": {"municipality": "Zsira"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://stkh.hu and look for your settlement in the waste calendar list on the home page. Use the settlement name exactly as it is shown there, for example 'Újkér'. Accents, spaces and capitalisation are ignored when matching.",
}

PARAM_TRANSLATIONS = {
    "en": {"municipality": "Settlement"},
}

PARAM_DESCRIPTIONS = {
    "en": {"municipality": "Name of the settlement as listed on stkh.hu"},
}

ICON_MAP = {
    "Szelektív": Icons.RECYCLING,
    "Zöldhulladék": Icons.GARDEN,
    "Vegyes": Icons.GENERAL_WASTE,
}

# Add your GitHub handle here to be notified and assigned on bug reports for
# this source:
# SOURCE_CODEOWNERS = ["@your-github-handle"]

HOMEPAGE_URL = "https://stkh.hu/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}

# Single-page settlement calendars look like ".../9472_Ujker_Hulladeknaptar2026.pdf".
# The leading number is a postcode, but it is not unique per settlement, so it is
# deliberately not used for the lookup.
PDF_LINK_PATTERN = re.compile(
    r"/\d{4}_([^/]+)_Hulladeknaptar(\d{4})\.pdf$", re.IGNORECASE
)
UPLOAD_PATH_PATTERN = re.compile(r"/uploads/(\d{4})/(\d{2})/")
YEAR_PATTERN = re.compile(r"(\d{4})\.\s*évi")
DATE_PATTERN = re.compile(r"\b(\d{2})\.(\d{2})\.")
MIXED_DAY_PATTERN = re.compile(r"Vegyes hulladékgyűjtési nap:([^\n]*)")

# Everything after this word is prose that contains stray numbers.
TABLE_END_MARKER = "Kérjük"

# Row labels of the collection table, mapped to the waste type reported by this source.
WASTE_TYPES = {
    "szelektív": "Szelektív",
    "zöldhulladék": "Zöldhulladék",
}
MIXED_WASTE_TYPE = "Vegyes"

MONTHS = {
    "januar": 1,
    "februar": 2,
    "marcius": 3,
    "aprilis": 4,
    "majus": 5,
    "junius": 6,
    "julius": 7,
    "augusztus": 8,
    "szeptember": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

WEEKDAYS = {
    "hetfo": 0,
    "kedd": 1,
    "szerda": 2,
    "csutortok": 3,
    "pentek": 4,
    "szombat": 5,
    "vasarnap": 6,
}


def normalize(value: str) -> str:
    """Fold a name to lowercase ASCII letters and digits only.

    Makes matching tolerant of accents, casing, spaces and hyphens, which differ
    between the link labels, the PDF file names and user input.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", stripped.lower())


@dataclass
class Calendar:
    """One edition of a settlement's waste calendar PDF."""

    year: int
    months: set = field(default_factory=set)
    dates: dict = field(default_factory=dict)
    weekday: int = -1


def extract_text(content: bytes) -> str:
    """Extract the full text of a calendar PDF."""
    reader = PdfReader(BytesIO(content))
    return "".join(page.extract_text() or "" for page in reader.pages)


def parse_calendar(text: str):
    """Parse a single calendar PDF into a Calendar, or None if unusable."""
    year_match = YEAR_PATTERN.search(text)
    if not year_match:
        return None
    calendar = Calendar(year=int(year_match.group(1)))

    table = text.split(TABLE_END_MARKER)[0]
    lowered = table.lower()

    # Locate the row label of every waste type present in this edition.
    positions = []
    for label, waste_type in WASTE_TYPES.items():
        index = lowered.find(label)
        if index >= 0:
            positions.append((index, waste_type))
    positions.sort()

    # The table header, in front of the first row label, lists the covered months.
    header = normalize(table[: positions[0][0]] if positions else table)
    calendar.months = {number for name, number in MONTHS.items() if name in header}
    if not calendar.months:
        calendar.months = set(range(1, 13))

    for i, (start, waste_type) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(table)
        days = set()
        for month, day in DATE_PATTERN.findall(table[start:end]):
            try:
                date(calendar.year, int(month), int(day))
            except ValueError:
                continue
            days.add((int(month), int(day)))
        calendar.dates[waste_type] = days

    # Mixed waste is published as a weekday rather than as a list of dates. Some
    # settlements say "körzetbeosztás szerint" (by district) instead; skip those.
    mixed_match = MIXED_DAY_PATTERN.search(text)
    if mixed_match:
        calendar.weekday = WEEKDAYS.get(normalize(mixed_match.group(1)), -1)

    return calendar


def edition_order(href: str):
    """Sort key that puts older editions of a calendar first.

    The upload folder (/uploads/YYYY/MM/) tells which edition is newer, which
    matters because a later edition supersedes the earlier one for the months it
    covers (collection days do get changed mid-year).
    """
    match = UPLOAD_PATH_PATTERN.search(href)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


class Source:
    def __init__(self, municipality: str):
        self._municipality: str = municipality

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        response = session.get(HOMEPAGE_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Index every settlement calendar linked from the home page, which always
        # points at the current editions. Both the file name stem and the link
        # label are indexed, because they occasionally disagree (typos).
        links: dict = {}
        names: set = set()
        for anchor in soup.select("a.hn.sor"):
            href = anchor.get("href") or ""
            match = PDF_LINK_PATTERN.search(href)
            if not match:
                # Per-street PDFs of the larger towns and district calendars use a
                # different layout and are not supported.
                continue
            label = anchor.get_text(strip=True)
            names.add(label or match.group(1))
            for key in {normalize(match.group(1)), normalize(label)}:
                if not key:
                    continue
                hrefs = links.setdefault(key, [])
                if href not in hrefs:
                    hrefs.append(href)

        key = normalize(self._municipality)
        if key not in links:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, sorted(names)
            )

        # A settlement normally has two editions (first and second half of the
        # year). They are not interchangeable: one may cover only part of the
        # year, and a newer one may change the collection days.
        editions = []
        for href in sorted(links[key], key=edition_order):
            pdf = session.get(href, timeout=60)
            pdf.raise_for_status()
            calendar = parse_calendar(extract_text(pdf.content))
            if calendar:
                editions.append(calendar)

        # Resolve every calendar month to the newest edition covering it.
        resolved: dict = {}
        for calendar in editions:
            for month in calendar.months:
                resolved[(calendar.year, month)] = calendar

        collections: set = set()
        for (year, month), calendar in resolved.items():
            for waste_type, days in calendar.dates.items():
                for day_month, day in days:
                    if day_month != month:
                        continue
                    collections.add((date(year, month, day), waste_type))

            if calendar.weekday >= 0:
                day = date(year, month, 1)
                day += timedelta(days=(calendar.weekday - day.weekday()) % 7)
                while day.month == month:
                    collections.add((day, MIXED_WASTE_TYPE))
                    day += timedelta(days=7)

        return [
            Collection(date=day, t=waste_type, icon=ICON_MAP.get(waste_type))
            for day, waste_type in sorted(collections)
        ]
