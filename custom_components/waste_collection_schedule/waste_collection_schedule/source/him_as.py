import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Haugaland Interkommunale Miljøverk (HIM)"
DESCRIPTION = (
    "Source for Haugaland Interkommunale Miljøverk (HIM) waste collection "
    "schedules, covering Haugesund and surrounding municipalities, Norway."
)
URL = "https://him.as"
COUNTRY = "no"
TEST_CASES = {
    "Leiv Eirikssons Gate 10": {"address": "Leiv Eirikssons Gate 10"},
    "ØVREGATA 170": {"address": "ØVREGATA 170"},
    # Several properties share this address
    "Haraldsgata 100": {"address": "Haraldsgata 100"},
}

CALENDAR_URL = "https://him.as/tommekalender/"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 30

# Maps the Norwegian data-type attribute used in the calendar table to an
# English waste type name.
WASTE_TYPE_MAP = {
    "matavfall": "Food waste",
    "restavfall": "Residual waste",
    "papir": "Paper",
    "plastemballasje": "Plastic packaging",
    "glassemballasje": "Glass packaging",
    "metallemballasje": "Metal packaging",
}

ICON_MAP = {
    "Food waste": Icons.ORGANIC,
    "Residual waste": Icons.GENERAL_WASTE,
    "Paper": Icons.PAPER,
    "Plastic packaging": Icons.PLASTIC_PACKAGING,
    "Glass packaging": Icons.GLASS,
    "Metal packaging": Icons.METAL,
}

# Norwegian month names as used in the calendar headings, e.g. "Juli 2026".
MONTH_MAP = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://him.as/tommekalender/, search for your address and use "
        "the address exactly as shown, e.g. 'Leiv Eirikssons Gate 10'."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address as shown on the HIM tømmekalender address search.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    }
}

SOURCE_CODEOWNERS = ["@bbr111"]


def _normalize(address: str) -> str:
    return " ".join(address.split()).casefold()


class Source:
    def __init__(self, address: str):
        self._address = address

    def _get(self, url: str, params: dict | None = None) -> BeautifulSoup:
        r = requests.get(
            url,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    def fetch(self) -> list[Collection]:
        soup = self._get(CALENDAR_URL, params={"adressesok": self._address})

        calendar_tables = soup.select("table.tommekalender__calendartable")
        if not calendar_tables:
            # No single exact match: either zero hits or several addresses
            # matched the search term. Both cases render a result table with
            # one row per candidate address instead of a calendar.
            candidates = soup.select("div.table-wrap table tbody tr td a[href]")
            # Several properties (e.g. sections of one building) can share the
            # exact same address, so picking it from the suggestions would
            # never narrow the search down. Follow the first exact match.
            exact = [
                a
                for a in candidates
                if _normalize(a.get_text()) == _normalize(self._address)
            ]
            if exact:
                soup = self._get(urljoin(CALENDAR_URL, str(exact[0]["href"])))
                calendar_tables = soup.select("table.tommekalender__calendartable")

            if not calendar_tables:
                suggestions = list(
                    dict.fromkeys(" ".join(a.get_text().split()) for a in candidates)
                )
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions
                )

        entries: list[Collection] = []
        for month_section in soup.select(
            "div.tommekalender__section.tommekalender__month"
        ):
            heading = month_section.find("h2")
            if heading is None:
                continue
            month_name, _, year_str = heading.get_text(strip=True).rpartition(" ")
            month = MONTH_MAP.get(month_name.strip().lower())
            if month is None or not year_str.isdigit():
                continue
            year = int(year_str)

            for day_cell in month_section.select(
                "td.tommekalender__calendartable__day--has-activities"
            ):
                date_div = day_cell.select_one(".tommekalender__calendartable__date")
                if date_div is None or not date_div.get_text(strip=True).isdigit():
                    continue
                day = int(date_div.get_text(strip=True))
                date = datetime.date(year, month, day)

                for item in day_cell.select(
                    "li.tommekalender__calendartable__listitem"
                ):
                    data_type = item.get("data-type")
                    if not isinstance(data_type, str):
                        continue
                    waste_type = WASTE_TYPE_MAP.get(data_type)
                    if waste_type is None:
                        continue
                    entries.append(
                        Collection(
                            date=date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries
