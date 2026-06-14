from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Piberbach"
DESCRIPTION = "Source for Piberbach, Austria."
URL = "https://www.piberbach.ooe.gv.at"
COUNTRY = "at"

TEST_CASES = {
    "Piberbacherstraße 20": {},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

BASE_URL = "https://www.piberbach.ooe.gv.at/system/web/kalender.aspx?bdatum=31.12.9999"

MAX_PAGES = 50

ICON_MAP = {
    "Bioabfall": Icons.ORGANIC,
    "Restabfall 2-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 4-wöchentlich": Icons.GENERAL_WASTE,
    "Restabfall 6-wöchentlich": Icons.GENERAL_WASTE,
    "Altpapier": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
}


class Source:
    def __init__(self):
        pass

    def _get_page(self, page_number: int):
        url = f"{BASE_URL}&page={page_number}"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def fetch(self):
        entries: list[Collection] = []
        seen_first_row: set[tuple[str, str]] = set()

        for page in range(MAX_PAGES):
            soup = self._get_page(page)
            table = soup.find("table", class_="ris_table")

            if table is None:
                break

            rows = table.find_all("tr")

            if len(rows) <= 1:
                break

            first_cells = rows[1].find_all("td")
            if len(first_cells) >= 2:
                first_row_key = (
                    first_cells[0].get_text(" ", strip=True),
                    first_cells[1].get_text(" ", strip=True),
                )
                if first_row_key in seen_first_row:
                    break
                seen_first_row.add(first_row_key)

            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                date_text = cells[0].get_text(" ", strip=True)
                collection_type = cells[1].get_text(" ", strip=True)

                if not date_text or not collection_type:
                    continue

                # Date format: "15.06.2026  (Montag)"
                date_text = date_text.split("(")[0].strip()

                try:
                    collection_date = datetime.strptime(date_text, "%d.%m.%Y").date()
                except ValueError:
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type),
                    )
                )

        if not entries:
            raise ValueError("Could not find any collection events.")

        # Remove duplicates
        unique_entries = {}
        for entry in entries:
            key = (entry.date, entry.type)
            unique_entries[key] = entry

        return sorted(unique_entries.values(), key=lambda x: x.date)
