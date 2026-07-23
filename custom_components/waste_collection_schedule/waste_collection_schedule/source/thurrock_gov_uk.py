import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule, weekday
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

WEEKDAYS = {
    "monday": MO,
    "tuesday": TU,
    "wednesday": WE,
    "thursday": TH,
    "friday": FR,
    "saturday": SA,
    "sunday": SU,
}

TITLE = "Thurrock"
DESCRIPTION = "Source for Thurrock."
URL = "https://www.thurrock.gov.uk/"
TEST_CASES = {
    "Camden Close Chadwell St Mary": {
        "street": "Camden Close",
        "town": "Chadwell St Mary",
    },
    "Abberton Way West Thurrock (street starting with A)": {
        "street": "Abberton Way",
        "town": "West Thurrock",
    },
}


ICON_MAP = {
    "Brown": Icons.ORGANIC,
    "Blue": Icons.PAPER,
    "Green": Icons.RECYCLING,
    "Grey": Icons.RECYCLING,
    "Green/Grey": Icons.RECYCLING,
}


# Streets beginning with A use the base URL (no letter suffix).
# All other letters append "-<letter>" to the base URL.
STREETS_BASE_URL = (
    "https://www.thurrock.gov.uk/household-bin-collection-days/street-names"
)
API_URL = "https://www.thurrock.gov.uk/household-bin-collection-days/household-bin-collection-weeks"

# Matches both ASCII hyphen-minus (-) and Unicode en-dash (–) with optional surrounding whitespace.
DATE_RANGE_RE = re.compile(r"\s*[-–—]\s*")
# Matches " and " or " / " (with optional extra whitespace) as bin-type separators.
BIN_SPLIT_RE = re.compile(r"\s*/\s*|\s+and\s+")


class Source:
    def __init__(self, street: str, town: str):
        self._street: str = street
        self._town: str = town
        self._day: weekday | None = None
        self._round: str | None = None

    def _streets_url(self) -> str:
        first = self._street[0].lower()
        if first == "a":
            return STREETS_BASE_URL
        return f"{STREETS_BASE_URL}-{first}"

    def fetch_day(self):
        if len(self._street) == 0:
            raise SourceArgumentRequired(
                "street",
                "Please provide a street name",
            )
        r = requests.get(self._streets_url(), verify=False)
        r.raise_for_status()
        soup = BeautifulSoup(
            r.text.replace("&nbsp;", " ").replace("\xa0", " "), "html.parser"
        )
        table = soup.select_one("table")
        if not table:
            raise Exception("street, town Table not found")
        towns = []
        streets = []
        day_str = None
        town_match = False
        street_match = False

        for row in table.select("tr")[1:]:
            cells = row.select("td")
            if len(cells) != 3:
                continue
            # Use rsplit to handle street names that contain ", " (e.g. parenthetical notes)
            parts = cells[0].text.strip().rsplit(", ", 1)
            if len(parts) != 2:
                continue
            street, town = parts

            towns.append(town.strip().casefold())
            streets.append(street.strip().casefold())
            if self._street.casefold() in street.casefold():
                street_match = True
            if self._town.casefold() in town.casefold():
                town_match = True
            if street_match and town_match:
                day_str = cells[1].text.strip()
                self._round = cells[2].text.strip()
                break
        if not day_str:
            if town_match:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street",
                    self._street,
                    streets,
                )
            raise SourceArgumentNotFoundWithSuggestions(
                "town",
                self._town,
                towns,
            )

        if day_str.lower() not in WEEKDAYS:
            raise Exception(f"Day ({day_str}) not a valid weekday")
        self._day = WEEKDAYS[day_str.lower()]

    def parse_date_range(self, range_str: str) -> tuple[date, date]:
        """Parse a date range such as '18 May - 22 May' or '25 May – 29 May'."""
        now = datetime.now()
        parts = DATE_RANGE_RE.split(range_str.strip())
        if len(parts) != 2:
            raise ValueError(f"Cannot parse date range: {range_str!r}")
        start_str, end_str = parts
        start_date = datetime.strptime(
            start_str.strip() + f" {now.year}", "%d %B %Y"
        ).date()
        end_date = datetime.strptime(
            end_str.strip() + f" {now.year}", "%d %B %Y"
        ).date()
        # Handle a range that straddles a year boundary (e.g. 30 Dec - 3 Jan)
        if start_date.month == 12 and end_date.month == 1:
            end_date = end_date.replace(year=start_date.year + 1)
        return start_date, end_date

    def fetch(self) -> list[Collection]:
        if self._day is None or self._round is None:
            self.fetch_day()
            assert self._day is not None
            assert self._round is not None

        r = requests.get(API_URL, verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text.replace("\xa0", " "), "html.parser")
        table = soup.select_one("table")
        if not table:
            raise Exception("Collection table not found")

        entries = []

        for tr in table.select("tr")[1:]:
            cells = tr.select("td")
            if len(cells) != 3:
                raise Exception("Invalid table format")
            start_date, end_date = self.parse_date_range(cells[0].text.strip())

            bin_text = cells[(1 if self._round == "A" else 2)].text.strip()
            bins = [b.strip() for b in BIN_SPLIT_RE.split(bin_text) if b.strip()]

            for bin_type in bins:
                for col_date in rrule(
                    WEEKLY,
                    dtstart=start_date,
                    until=end_date,
                    byweekday=self._day,
                ):
                    entries.append(
                        Collection(
                            date=col_date.date(),
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )

        return entries
