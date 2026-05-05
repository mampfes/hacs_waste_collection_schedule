import re
from datetime import date

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Bolsover District Council"
DESCRIPTION = "Source for Bolsover District Council, UK."
URL = "https://www.bolsover.gov.uk"

TEST_CASES = {
    "Calendar A, Wednesday": {"calendar": "a", "collection_day": "wednesday"},
    "Calendar B, Thursday": {"calendar": "b", "collection_day": "thursday"},
}

VALID_CALENDARS = ["a", "b"]
VALID_DAYS = ["tuesday", "wednesday", "thursday", "friday"]

DAY_COLUMNS = {
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}

ICON_MAP = {
    "Black": "mdi:trash-can",
    "Burgundy": "mdi:recycle",
    "Green": "mdi:leaf",
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Check your bin calendar letter (A or B) and collection day (Tuesday–Friday) on the Bolsover website at https://www.bolsover.gov.uk/services/b/bins-and-recycling/.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "calendar": "Your bin calendar letter: 'a' or 'b'.",
        "collection_day": "Your collection day: tuesday, wednesday, thursday, or friday.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "calendar": "Calendar",
        "collection_day": "Collection Day",
    },
}


def _get_icon(bin_type: str) -> str | None:
    for key, icon in ICON_MAP.items():
        if key.lower() in bin_type.lower():
            return icon
    return None


class Source:
    def __init__(self, calendar: str, collection_day: str):
        self._calendar = calendar.strip().lower()
        self._collection_day = collection_day.strip().lower()

        if self._calendar not in VALID_CALENDARS:
            raise SourceArgumentNotFoundWithSuggestions(
                "calendar", self._calendar, suggestions=VALID_CALENDARS
            )
        if self._collection_day not in VALID_DAYS:
            raise SourceArgumentNotFoundWithSuggestions(
                "collection_day", self._collection_day, suggestions=VALID_DAYS
            )

    def fetch(self) -> list[Collection]:
        r = requests.get(
            f"https://www.bolsover.gov.uk/waste-bins-recycling/bin-calendar-{self._calendar}",
            impersonate="chrome124",
            timeout=30,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        col_idx = DAY_COLUMNS[self._collection_day]

        entries: list[Collection] = []

        for table in soup.find_all("table"):
            headers = [
                th.text.strip().lower()
                for th in table.find("tr").find_all(["th", "td"])
            ]

            # Skip non-collection tables (e.g. Christmas amendments)
            if "bin" not in headers[0].lower() if headers else True:
                continue

            # Find the month heading before this table
            heading = table.find_previous("h2")
            if not heading:
                continue

            match = re.match(r"(\w+)\s+(\d{4})", heading.text.strip())
            if not match:
                continue

            month_name, year_str = match.groups()
            if month_name not in MONTHS:
                continue

            month = MONTHS[month_name]
            year = int(year_str)

            for row in table.find_all("tr")[1:]:
                cells = [td.text.strip() for td in row.find_all(["td", "th"])]
                if len(cells) <= col_idx:
                    continue

                bin_label = cells[0]
                if "no collection" in bin_label.lower():
                    continue

                day_str = cells[col_idx]
                # Strip annotations like "(No collection)"
                day_str = re.sub(r"\(.*?\)", "", day_str).strip()
                if not day_str or not day_str.isdigit():
                    continue

                day = int(day_str)
                try:
                    collection_date = date(year, month, day)
                except ValueError:
                    continue

                # Split combined bin types like "Green / Burgundy" or "Burgundy / Black"
                bin_types = [b.strip() for b in bin_label.split("/")]
                for bt in bin_types:
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=bt,
                            icon=_get_icon(bt),
                        )
                    )

        return entries
