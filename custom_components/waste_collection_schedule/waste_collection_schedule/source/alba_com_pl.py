import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "ALBA Swarzędz"
DESCRIPTION = "Source for ALBA waste collection in Swarzędz municipality, Poland."
URL = "https://www.alba.com.pl"
COUNTRY = "pl"

TEST_CASES = {
    "Bogucin, Boczna 7": {
        "city": "BOGUCIN",
        "street": "BOCZNA",
        "number": "7",
    },
    "Gortatowo, Królewska 12": {
        "city": "GORTATOWO",
        "street": "KRÓLEWSKA",
        "number": "12",
    },
    "Swarzędz, Józefa Rivoliego 2": {
        "city": "SWARZĘDZ",
        "street": "JÓZEFA RIVOLIEGO",
        "number": "2",
    },
}

SOURCE_CODEOWNERS = ["@kamilos-dev"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz "
        "and use the schedule search form. Select your city, street and house "
        "number from the dropdowns and use those exact values (uppercase) as "
        "the source arguments."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City",
        "street": "Street",
        "number": "House number",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City name in uppercase, e.g. SWARZĘDZ",
        "street": "Street name in uppercase, e.g. JÓZEFA RIVOLIEGO",
        "number": "House/building number, e.g. 2",
    },
}

ICON_MAP = {
    "Zmieszane odpady komunalne": Icons.GENERAL_WASTE,
    "Metale i tworzywa sztuczne": Icons.RECYCLING,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Bioodpady": Icons.ORGANIC,
    "Bioodpady - Drzewka świąteczne": Icons.CHRISTMAS_TREE,
    "Odpady wystawkowe": Icons.BULKY,
}

API_BASE = "https://sepan-wroclaw.alba.com.pl/harmonogram2025_swarzedz"

POLISH_MONTHS = {
    "STYCZEŃ": 1,
    "LUTY": 2,
    "MARZEC": 3,
    "KWIECIEŃ": 4,
    "MAJ": 5,
    "CZERWIEC": 6,
    "LIPIEC": 7,
    "SIERPIEŃ": 8,
    "WRZESIEŃ": 9,
    "PAŹDZIERNIK": 10,
    "LISTOPAD": 11,
    "GRUDZIEŃ": 12,
}


class Source:
    def __init__(self, city: str, street: str, number: str):
        self._city = city.upper().strip()
        self._street = street.upper().strip()
        self._number = str(number).strip()

    def fetch(self) -> list[Collection]:
        city_id = self._resolve_id(
            f"{API_BASE}/addresses/cities",
            self._city,
            "city",
        )
        street_id = self._resolve_id(
            f"{API_BASE}/addresses/streets/{city_id}",
            self._street,
            "street",
        )
        address_id = self._resolve_id(
            f"{API_BASE}/addresses/numbers/{city_id}/{street_id}",
            self._number,
            "number",
        )

        report = requests.get(
            f"{API_BASE}/reports",
            params={"type": "html", "id": address_id},
            timeout=30,
        ).json()

        html = requests.get(report["filePath"], timeout=30).text
        entries = self._parse(html)

        if not entries:
            raise ValueError("No waste collection dates found in the schedule")

        return entries

    def _resolve_id(self, url: str, value: str, arg_name: str) -> int:
        items = requests.get(url, timeout=30).json()
        suggestions = [str(i["value"]) for i in items]
        match = next(
            (i for i in items if str(i["value"]).upper().strip() == value),
            None,
        )
        if not match:
            raise SourceArgumentNotFoundWithSuggestions(arg_name, value, suggestions)
        return match["id"]

    def _parse(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")

        table = None
        headers: list[str] = []
        for t in soup.find_all("table"):
            ths = [th.get_text(strip=True) for th in t.find_all("th")]
            if "Miesiąc" in ths:
                table = t
                headers = ths[1:]
                break

        if table is None:
            raise ValueError("Schedule table not found in HTML response")

        entries: list[Collection] = []
        for row in table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue

            parts = cells[0].get_text(strip=True).split()
            if len(parts) < 2:
                continue

            month = POLISH_MONTHS.get(parts[0])
            if not month:
                continue
            year = int(parts[-1])

            for i, cell in enumerate(cells[1:]):
                if i >= len(headers):
                    break
                days_text = cell.get_text(strip=True)
                if not days_text:
                    continue

                waste_type = headers[i]
                for day_str in days_text.split(","):
                    day_str = day_str.strip()
                    if not day_str.isdigit():
                        continue
                    try:
                        entries.append(
                            Collection(
                                date=datetime.date(year, month, int(day_str)),
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
                    except ValueError:
                        pass

        return entries
