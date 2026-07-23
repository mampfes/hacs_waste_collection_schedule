import re
from datetime import date, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "City of Stamford, CT"
DESCRIPTION = (
    "Source for the City of Stamford, CT garbage and recycling pickup day lookup."
)
URL = "https://www.stamfordct.gov/government/operations/recycling-and-sanitation/about/recycling-and-garbage-schedule"
COUNTRY = "us"

TEST_CASES = {
    "Parker Ave": {"street": "Parker Ave"},
    "Washington Blvd, house 200": {"street": "Washington Blvd", "house_number": 200},
    "Washington Blvd, house 500": {"street": "Washington Blvd", "house_number": 500},
}

ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

WEEKDAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}

BASE_URL = "https://stamfordapps.org/garbagerecycling/"
WEEKS_TO_GENERATE = 26

RANGE_RE = re.compile(r"(\d+)(?:\s*TO\s*(\d+))?\s*(BOTH|ODD|EVEN)?")

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the City of Stamford Garbage and Recycling Lookup "
        "(https://stamfordapps.org/garbagerecycling/default.asp) to find your street. "
        "Enter just the street name (e.g. 'Parker' for 'Parker Ave'), leaving out the "
        "street suffix (Ave, St, Rd, etc.) and the house number. If your street has "
        "multiple pickup-day ranges, also provide your house number; the source will "
        "tell you the available ranges if it is required but missing."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": (
            "Street name only, without the house number or street suffix "
            "(e.g. 'Parker' or 'Parker Ave' for '123 Parker Ave')."
        ),
        "house_number": (
            "Optional house number. Required only if pickup days differ across "
            "house-number ranges on this street; the error message will list the "
            "available ranges if so."
        ),
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street Name",
        "house_number": "House Number (optional)",
    }
}


class Source:
    def __init__(self, street: str, house_number: str | int | None = None):
        self._street = street.strip()
        self._house_number: int | None = None
        if house_number not in (None, ""):
            try:
                self._house_number = int(str(house_number).strip())
            except ValueError:
                raise SourceArgumentNotFound(
                    "house_number",
                    house_number,
                    message_addition="house_number must be a whole number.",
                ) from None

    def _resolve_street_url(self, session: requests.Session) -> str:
        params = {"STREET": self._street, "CHECKED": "TRUE"}
        r = session.get(
            urljoin(BASE_URL, "StreetMultipleResults.asp"), params=params, timeout=30
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        matches: dict[str, str] = {}
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "StreetResultsDetails.asp" not in href:
                continue
            row = link.find_parent("tr")
            name_cell = row.find_all("td")[0] if row is not None else None
            name = (
                name_cell.get_text(strip=True)
                if name_cell is not None
                else link.get_text(strip=True)
            )
            matches[name] = urljoin(BASE_URL, href)

        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                argument="street", value=self._street, suggestions=[]
            )

        if len(matches) == 1:
            return next(iter(matches.values()))

        upper_query = self._street.upper()
        exact = [name for name in matches if name == upper_query]
        if len(exact) == 1:
            return matches[exact[0]]

        starts_with = [name for name in matches if name.startswith(upper_query + " ")]
        if len(starts_with) == 1:
            return matches[starts_with[0]]

        raise SourceArgAmbiguousWithSuggestions(
            argument="street", value=self._street, suggestions=sorted(matches.keys())
        )

    @staticmethod
    def _find_section_table(soup: BeautifulSoup, label: str):
        for table in soup.select("table table"):
            text = table.get_text(" ", strip=True).upper()
            if f"{label} PICKUP INFORMATION" in text:
                return table
        return None

    @staticmethod
    def _iter_rows(table):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) != 3:
                continue
            range_text = cells[0].get_text(" ", strip=True)
            if not any(ch.isdigit() for ch in range_text):
                # header / title rows have no digits in the first cell
                continue
            match = RANGE_RE.search(range_text.upper())
            if not match:
                continue
            low = int(match.group(1))
            high = int(match.group(2)) if match.group(2) else low
            parity = match.group(3) or "BOTH"
            day_text = cells[2].get_text(" ", strip=True).upper()
            yield low, high, parity, day_text

    def _determine_day(self, table, waste_type: str) -> str | None:
        rows = list(self._iter_rows(table))
        if not rows:
            return None

        def describe(row):
            low, high, parity, day_text = row
            return f"{low}-{high} ({parity.lower()}): {day_text.title()}"

        if self._house_number is not None:
            matching = [
                day_text
                for (low, high, parity, day_text) in rows
                if low <= self._house_number <= high
                and (
                    parity == "BOTH"
                    or (parity == "ODD" and self._house_number % 2 == 1)
                    or (parity == "EVEN" and self._house_number % 2 == 0)
                )
            ]
            if not matching:
                raise SourceArgumentNotFoundWithSuggestions(
                    argument="house_number",
                    value=self._house_number,
                    suggestions=[describe(row) for row in rows],
                )
            day_text = matching[0]
        else:
            distinct = {row[3] for row in rows}
            if len(distinct) > 1:
                raise SourceArgumentRequiredWithSuggestions(
                    argument="house_number",
                    reason=(
                        f"{waste_type} pickup day varies by house number on "
                        f"{self._street}"
                    ),
                    suggestions=[describe(row) for row in rows],
                )
            day_text = rows[0][3]

        if day_text not in WEEKDAYS:
            # e.g. "NO GARBAGE PICKUP" / "NO RECYCLING PICKUP"
            return None
        return day_text

    @staticmethod
    def _weekly_collections(day_text: str, waste_type: str) -> list[Collection]:
        weekday = WEEKDAYS[day_text]
        today = date.today()
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)
        icon = ICON_MAP.get(waste_type)
        return [
            Collection(date=next_date + timedelta(weeks=i), t=waste_type, icon=icon)
            for i in range(WEEKS_TO_GENERATE)
        ]

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        detail_url = self._resolve_street_url(session)
        r = session.get(detail_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        entries: list[Collection] = []
        for label, waste_type in (("RECYCLING", "Recycling"), ("GARBAGE", "Garbage")):
            table = self._find_section_table(soup, label)
            if table is None:
                continue
            day_text = self._determine_day(table, waste_type)
            if day_text is None:
                continue
            entries.extend(self._weekly_collections(day_text, waste_type))

        if not entries:
            raise SourceArgumentNotFound(
                argument="street",
                value=self._street,
                message_addition=(
                    "no garbage or recycling pickup could be determined for this "
                    "address; it may not be covered by the residential lookup "
                    "(e.g. condominiums are excluded)"
                ),
            )

        return entries
