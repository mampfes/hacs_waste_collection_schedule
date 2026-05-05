import re
from datetime import datetime
from io import BytesIO

import requests
from pypdf import PdfReader
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Redbridge Council"
DESCRIPTION = "Source for redbridge.gov.uk services for Redbridge Council, UK."
URL = "https://redbridge.gov.uk"
TEST_CASES = {
    "council office recycling only": {"uprn": 10034922090},
    "refuse and recycling only": {"uprn": 10013585215},
    "a church vicarage, garden, recycling, refuse": {"uprn": 10034912354},
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
    "FOOD": "mdi:food-apple",
}

KNOWN_SERVICES = {"REFUSE", "RECYCLING", "GARDEN", "FOOD"}


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def _extract_collections_from_text(text: str) -> list[Collection]:
    # Normalise and split into non‑empty trimmed lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Headers and structure
    month_regex = re.compile(
        r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})$",
        re.I,
    )
    weekday_header_regex = re.compile(
        r"^(Sun\s+Mon\s+Tue\s+Wed\s+Thu\s+Fri\s+Sat)$", re.I
    )

    # A day row contains one or more day numbers separated by spaces, e.g. "1 2" or "3 4 5 6 7"
    day_group_regex = re.compile(r"^(?:\d{1,2})(?:\s+\d{1,2})*$")

    # PDF lists only the type name per line, e.g. "Refuse", "Food", "Garden", "Recycling"
    service_regex = re.compile(r"^(.+)$")

    current_month_name: str | None = None
    current_year: int | None = None

    def month_number(name: str) -> int:
        return datetime.strptime(name, "%B").month

    entries: list[Collection] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect month header, e.g. "March 2026"
        m = month_regex.match(line)
        if m:
            current_month_name = m.group(1)
            current_year = int(m.group(2))
            i += 1
            continue

        # Skip weekday header rows and other non‑data noise
        lower = line.lower()
        if (
            weekday_header_regex.match(line)
            or lower.startswith("london borough of redbridge")
            or "your collection schedule" in lower
        ):
            i += 1
            continue

        # Detect a calendar day ROW (e.g. "1 2" or "3 4 5 6 7") once we know the month/year
        if current_month_name and current_year and day_group_regex.match(line):
            # Parse all day numbers on the row
            days: list[int] = []
            for token in line.split():
                try:
                    d = int(token)
                    if 1 <= d <= 31:
                        days.append(d)
                except ValueError:
                    pass

            # Gather following service lines until next structural boundary
            services: list[str] = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                lower_next = next_line.lower()

                if (
                    month_regex.match(next_line)
                    or weekday_header_regex.match(next_line)
                    or day_group_regex.match(next_line)
                    or "your collection schedule" in lower_next
                ):
                    break

                s = service_regex.match(next_line)
                if s:
                    wt = s.group(1).strip()
                    key = wt.split(" ")[0].upper()
                    if key in KNOWN_SERVICES:
                        services.append(wt)
                j += 1

            # For this layout, all services on the row belong to the last day number
            if days and services:
                month = month_number(current_month_name)
                target_day = max(days)
                date = datetime(current_year, month, target_day).date()
                for wt in services:
                    key = wt.split(" ")[0].upper()
                    entries.append(Collection(date=date, t=wt, icon=ICON_MAP.get(key)))

            i = j
            continue

        i += 1

    return entries


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        r = requests.get(
            "https://my.redbridge.gov.uk/RecycleRefuse/GetFile",
            params={"uprn": self._uprn},
        )
        r.raise_for_status()

        pdf_text = _extract_text_from_pdf(r.content)
        return _extract_collections_from_text(pdf_text)
