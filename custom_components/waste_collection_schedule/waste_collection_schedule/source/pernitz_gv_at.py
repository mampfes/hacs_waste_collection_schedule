import datetime
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Marktgemeinde Pernitz"
DESCRIPTION = "Source for Marktgemeinde Pernitz, Austria."
URL = "https://www.pernitz.gv.at"
COUNTRY = "at"
SOURCE_CODEOWNERS = ["@bbr111"]

TEST_CASES: dict[str, dict] = {
    "Rayon 1": {"rayon": 1},
    "Rayon 2": {"rayon": 2},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gelber Container": Icons.PLASTIC_PACKAGING,
    "Papier": Icons.PAPER,
}

PARAM_TRANSLATIONS = {
    "en": {
        "rayon": "Rayon (collection zone)",
    },
    "de": {
        "rayon": "Rayon (Abfuhrbezirk)",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "rayon": "The general waste (Restmüll) collection zone, 1 or 2, that your street belongs to. "
        "See the street list at https://www.pernitz.gv.at/muellabfuhr/ to determine your zone.",
    },
    "de": {
        "rayon": "Der Restmüll-Abfuhrbezirk (Rayon), 1 oder 2, zu dem Ihre Straße gehört. "
        "Die Straßenliste finden Sie unter https://www.pernitz.gv.at/muellabfuhr/.",
    },
}

API_URL = "https://www.pernitz.gv.at/muellabfuhr/"

DATE_REGEX = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")

# Number of upcoming months to generate for collections that are only
# announced as a recurring rule (e.g. "every 1st Saturday of the month")
# instead of an explicit list of dates.
_RECURRING_MONTHS_AHEAD = 18


class Source:
    def __init__(self, rayon: int):
        rayon = int(rayon)
        if rayon not in (1, 2):
            raise SourceArgumentNotFoundWithSuggestions("rayon", rayon, [1, 2])
        self._rayon = rayon

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        accordion_items = soup.find_all("div", class_="wp-block-advgb-accordion-item")
        sections: dict[str, Tag] = {}
        for item in accordion_items:
            header_el = item.find("h4", class_="advgb-accordion-header-title")
            if header_el is None:
                continue
            header = header_el.get_text(strip=True)
            sections[header] = item

        entries: list[Collection] = []

        entries += self._parse_date_table(
            sections.get(f"Restmüll Rayon {self._rayon}"), "Restmüll"
        )
        entries += self._parse_date_table(sections.get("Biotonne"), "Biotonne")
        entries += self._parse_date_table(sections.get("Gelber Sack"), "Gelber Sack")
        entries += self._parse_date_table(
            sections.get("Gelber Container"), "Gelber Container"
        )

        # Paper collection is only published as a recurring rule ("every 1st
        # Saturday of the month"), not as a list of explicit dates.
        entries += self._first_weekday_of_month_series(
            "Papier",
            weekday=5,  # Saturday
        )

        return entries

    @staticmethod
    def _parse_date_table(item: Tag | None, waste_type: str) -> list[Collection]:
        collections: list[Collection] = []
        if item is None:
            return collections
        table = item.find("table")
        if table is None:
            return collections
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            row_text = " ".join(cell.get_text(strip=True) for cell in cells)
            match = DATE_REGEX.search(row_text)
            if not match:
                continue
            day, month, year = (int(group) for group in match.groups())
            try:
                date = datetime.date(year, month, day)
            except ValueError:
                continue
            collections.append(
                Collection(date=date, t=waste_type, icon=ICON_MAP.get(waste_type))
            )
        return collections

    @staticmethod
    def _first_weekday_of_month_series(
        waste_type: str, weekday: int
    ) -> list[Collection]:
        collections: list[Collection] = []
        today = datetime.date.today()
        year, month = today.year, today.month
        for _ in range(_RECURRING_MONTHS_AHEAD):
            first_day = datetime.date(year, month, 1)
            days_ahead = (weekday - first_day.weekday()) % 7
            collection_date = first_day + datetime.timedelta(days=days_ahead)
            collections.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )
            month += 1
            if month > 12:
                month = 1
                year += 1
        return collections
