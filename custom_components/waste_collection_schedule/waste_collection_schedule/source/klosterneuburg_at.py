import ast
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Stadtgemeinde Klosterneuburg"
DESCRIPTION = "Source for Stadtgemeinde Klosterneuburg waste collection."
URL = "https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender"
COUNTRY = "at"

TEST_CASES = {
    "Kierlinger Straße 10": {
        "street": "Kierlinger Straße",
        "house_number": "10",
    },
    "Adalbert Stifter-Gasse 1": {
        "street": "Adalbert Stifter-Gasse",
        "house_number": "1",
    },
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Papiermüll": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
    "Sperrmüll": "mdi:sofa",
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as shown on the Klosterneuburg website",
        "house_number": "House number",
    },
}

PAGE_URL = "https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender"
CALENDAR_URL = "https://www.klosterneuburg.at/system/web/kalender.aspx"


class Source:
    def __init__(self, street: str, house_number: str | int):
        self._street = street.strip()
        self._house_number = str(house_number).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1: GET the main page to extract street/house/zone data
        r = session.get(PAGE_URL, timeout=30)
        r.raise_for_status()
        r.encoding = "utf-8"

        # Parse strassenArr (street → house numbers → zone IDs)
        start = r.text.index("strassenArr = [") + len("strassenArr = ")
        depth = 0
        for i, c in enumerate(r.text[start:], start):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
            if depth == 0:
                end = i + 1
                break
        street_data = ast.literal_eval(r.text[start:end])

        # Parse street name dropdown
        select_match = re.search(
            r'id="\d+_boxmuellkalenderstrassedd"[^>]*>(.*?)</select>',
            r.text,
            re.DOTALL,
        )
        opts = re.findall(r'value="(\d+)"[^>]*>(.*?)<', select_match.group(1))
        street_map = {name: int(val) for val, name in opts}

        # Find matching street
        street_id = None
        for name, sid in street_map.items():
            if name.lower().replace(" ", "") == self._street.lower().replace(" ", ""):
                street_id = sid
                break

        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, list(street_map.keys())
            )

        # Find matching house number and get typIds
        typ_ids = None
        house_numbers = []
        for street in street_data:
            if street[0] == street_id:
                for hnr in street[1]:
                    house_numbers.append(str(hnr[1]))
                    if str(hnr[1]) == self._house_number:
                        typ_ids = hnr[2]
                break

        if typ_ids is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, house_numbers
            )

        # Extract menuonr from the calendar URL pattern
        menu_match = re.search(r"menuonr=(\d+)", r.text)
        menuonr = menu_match.group(1) if menu_match else "226582740"

        # Step 2: GET the calendar page
        r = session.get(
            CALENDAR_URL,
            params={"sprache": 1, "menuonr": menuonr, "typids": typ_ids},
            timeout=30,
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        # Step 3: Parse the HTML table
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        entries = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            date_text = cells[0].get_text(strip=True)
            waste_type = cells[1].get_text(strip=True)

            # Parse date: "20.04.2026  (Montag)" → extract date part
            date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_text)
            if not date_match:
                continue

            date = datetime.strptime(date_match.group(1), "%d.%m.%Y").date()
            icon = next(
                (v for k, v in ICON_MAP.items() if k.lower() in waste_type.lower()),
                None,
            )
            entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
