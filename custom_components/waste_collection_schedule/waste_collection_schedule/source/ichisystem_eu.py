"""Source for Hemar (ichisystem.eu), Poland."""

import re
from datetime import date, datetime
from html.parser import HTMLParser
from typing import List, Optional

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Hemar (ichisystem.eu)"
DESCRIPTION = (
    "Source for the Hemar waste collection schedule platform "
    "(harmonogram.ichisystem.eu) used by several Polish municipalities."
)
URL = "https://harmonogram.ichisystem.eu/hemar/"
COUNTRY = "pl"

TEST_CASES = {
    "Pobiedziska, Boczna 2": {
        "city": "Pobiedziska",
        "street": "Boczna",
        "house_number": "2",
    },
    "Pobiedziska, Dworcowa 1": {
        "city": "POBIEDZISKA",
        "street": "DWORCOWA",
        "house_number": "1",
    },
}

EXTRA_INFO = [
    {
        "title": "Pobiedziska",
        "url": "https://harmonogram.ichisystem.eu/hemar/",
        "default_params": {"city": "Pobiedziska"},
    },
    {
        "title": "Kiszkowo",
        "url": "https://harmonogram.ichisystem.eu/hemar/",
        "default_params": {"city": "Kiszkowo"},
    },
]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://harmonogram.ichisystem.eu/hemar/ and pick your city, "
        "street, and house number from the dropdowns. Use those exact values "
        "for the city, street, and house_number arguments (matching is "
        "case-insensitive)."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City / town name as listed on the Hemar portal.",
        "street": "Street name as listed on the Hemar portal.",
        "house_number": "House number as listed on the Hemar portal.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "house_number": "House number",
    },
}

ICON_MAP = {
    "zmieszane": Icons.GENERAL_WASTE,
    "papier": Icons.PAPER,
    "metale": Icons.METAL,
    "tworzywa": Icons.RECYCLING,
    "szk": Icons.GLASS_COLORED,
    "bio": Icons.ORGANIC,
    "drzewka": Icons.CHRISTMAS_TREE,
    "wystawkow": Icons.BULKY,
    "gabaryt": Icons.BULKY,
    "popi": Icons.GENERAL_WASTE,
    "choink": Icons.CHRISTMAS_TREE,
}

API_BASE = "https://harmonogram.ichisystem.eu/hemar"

# Polish month names as used in the schedule HTML, mapped to month numbers.
PL_MONTHS = {
    "styczen": 1,
    "luty": 2,
    "marzec": 3,
    "kwiecien": 4,
    "maj": 5,
    "czerwiec": 6,
    "lipiec": 7,
    "sierpien": 8,
    "wrzesien": 9,
    "pazdziernik": 10,
    "listopad": 11,
    "grudzien": 12,
}


def _strip_pl(text: str) -> str:
    """Normalise Polish text: lowercase + drop diacritics + collapse whitespace."""
    table = str.maketrans(
        {
            "ą": "a",
            "Ą": "a",
            "ć": "c",
            "Ć": "c",
            "ę": "e",
            "Ę": "e",
            "ł": "l",
            "Ł": "l",
            "ń": "n",
            "Ń": "n",
            "ó": "o",
            "Ó": "o",
            "ś": "s",
            "Ś": "s",
            "ź": "z",
            "Ź": "z",
            "ż": "z",
            "Ż": "z",
        }
    )
    return re.sub(r"\s+", " ", text.translate(table).lower()).strip()


def _icon_for(waste_type: str) -> Optional[str]:
    key = _strip_pl(waste_type)
    for needle, icon in ICON_MAP.items():
        if needle in key:
            return icon
    return None


class _ScheduleTableParser(HTMLParser):
    """Extract the first schedule table from the Hemar report HTML.

    The table has a header row with waste-type names and one body row per
    month. The first cell of each body row is a Polish month name; the
    remaining cells contain comma-separated day numbers (or empty).
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_table = False
        self._in_thead = False
        self._in_tbody = False
        self._in_tr = False
        self._in_cell = False
        self._cell_text: List[str] = []
        self._current_row: List[str] = []
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self._captured = False

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        if self._captured:
            return
        if tag == "table":
            self._in_table = True
        elif tag == "thead" and self._in_table:
            self._in_thead = True
        elif tag == "tbody" and self._in_table:
            self._in_tbody = True
        elif tag == "tr" and self._in_table:
            self._in_tr = True
            self._current_row = []
        elif tag in ("td", "th") and self._in_tr:
            self._in_cell = True
            self._cell_text = []

    def handle_endtag(self, tag: str):  # type: ignore[override]
        if self._captured:
            return
        if tag in ("td", "th") and self._in_cell:
            self._current_row.append("".join(self._cell_text).strip())
            self._in_cell = False
        elif tag == "tr" and self._in_tr:
            if self._in_thead:
                # Take the longest header row (real header may be the 2nd row).
                if len(self._current_row) > len(self.headers):
                    self.headers = self._current_row
            elif self._in_tbody:
                self.rows.append(self._current_row)
            self._in_tr = False
        elif tag == "thead":
            self._in_thead = False
        elif tag == "tbody":
            self._in_tbody = False
            if self.headers and self.rows:
                self._captured = True
        elif tag == "table":
            self._in_table = False

    def handle_data(self, data: str):  # type: ignore[override]
        if self._in_cell:
            self._cell_text.append(data)


class Source:
    def __init__(self, city: str, street: str, house_number: str):
        self._city = str(city).strip()
        self._street = str(street).strip()
        self._house_number = str(house_number).strip()
        self._session = requests.Session()

    def _get_json(self, path: str):
        r = self._session.get(f"{API_BASE}{path}", timeout=30)
        r.raise_for_status()
        return r.json()

    def _find(self, items, target: str, arg_name: str):
        norm_target = _strip_pl(target)
        for item in items:
            if _strip_pl(item["value"]) == norm_target:
                return item
        suggestions = [item["value"] for item in items]
        raise SourceArgumentNotFoundWithSuggestions(
            arg_name, target, suggestions=suggestions
        )

    def fetch(self) -> List[Collection]:
        cities = self._get_json("/addresses/cities")
        city = self._find(cities, self._city, "city")

        streets = self._get_json(f"/addresses/streets/{city['id']}")
        street = self._find(streets, self._street, "street")

        numbers = self._get_json(f"/addresses/numbers/{city['id']}/{street['id']}")
        number = self._find(numbers, self._house_number, "house_number")

        years = self._get_json("/years")
        if not years:
            return []

        today = date.today()
        entries: List[Collection] = []
        seen: set = set()

        for year_entry in years:
            year_id = year_entry["id"]
            year_value = int(year_entry["value"])
            report = self._session.get(
                f"{API_BASE}/reports",
                params={
                    "type": "html",
                    "id": number["id"],
                    "responseType": "json",
                    "token": number["token"],
                    "yearId": year_id,
                },
                timeout=30,
            )
            report.raise_for_status()
            payload = report.json()
            if payload.get("status") != "success" or not payload.get("filePath"):
                continue

            html_resp = self._session.get(payload["filePath"], timeout=30)
            html_resp.raise_for_status()
            html_resp.encoding = "utf-8"

            for collection in self._parse_schedule(html_resp.text, year_value):
                key = (collection.date, collection.type)
                if key in seen:
                    continue
                seen.add(key)
                # Skip dates more than 30 days in the past to keep payload small.
                if (today - collection.date).days > 30:
                    continue
                entries.append(collection)

        return entries

    @staticmethod
    def _parse_schedule(html: str, year: int) -> List[Collection]:
        parser = _ScheduleTableParser()
        parser.feed(html)

        if not parser.headers or not parser.rows:
            return []

        # First header column is the month name; remaining are waste types.
        waste_types = parser.headers[1:]
        results: List[Collection] = []

        for row in parser.rows:
            if not row:
                continue
            month_name = _strip_pl(row[0])
            month = PL_MONTHS.get(month_name)
            if month is None:
                continue
            for col_idx, cell in enumerate(row[1:], start=0):
                if col_idx >= len(waste_types):
                    break
                cell = cell.strip()
                if not cell:
                    continue
                waste_type = waste_types[col_idx].strip()
                for piece in re.split(r"[,;/]", cell):
                    piece = piece.strip()
                    if not piece.isdigit():
                        continue
                    day = int(piece)
                    try:
                        collection_date = datetime(year, month, day).date()
                    except ValueError:
                        continue
                    results.append(
                        Collection(
                            date=collection_date,
                            t=waste_type,
                            icon=_icon_for(waste_type),
                        )
                    )
        return results
