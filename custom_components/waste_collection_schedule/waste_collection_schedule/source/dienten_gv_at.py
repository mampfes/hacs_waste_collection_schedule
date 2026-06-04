from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Dienten am Hochkönig"
DESCRIPTION = "Waste collection schedule for Dienten am Hochkönig, Austria."
URL = "https://www.dienten.gv.at"

TEST_CASES = {
    #no input required as the waste collectoin site (dienten.gv.at) does not have any address specific requirement
    "Dorf 53": {"address": "Dorf 53"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

BASE_URL = (
    "https://www.dienten.gv.at/system/web/kalender.aspx"
)

MAX_PAGES = 3

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Gelbe Tonne": Icons.RECYCLING,
    "Gelber Sack": Icons.RECYCLING,
    "Papier Gewerbe": Icons.PAPER,
    "Karton Gewerbe": Icons.PAPER,
}


class Source:
    def __init__(self, address: str):
        pass

    def _get_page(self, page_number: int):
        url = f"{BASE_URL}&page={page_number}"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        return BeautifulSoup(response.text, "html.parser")

    def fetch(self):
        entries: list[Collection] = []

        for page in range(MAX_PAGES):
            soup = self._get_page(page)

            table = soup.find("table", class_="ris_table")

            if table is None:
                continue

            rows = table.find_all("tr")

            if len(rows) <= 1:
                continue

            for row in rows[1:]:
                cells = row.find_all("td")

                if len(cells) < 2:
                    continue

                date_text = cells[0].get_text(" ", strip=True)
                collection_type = cells[1].get_text(" ", strip=True)

                if not date_text or not collection_type:
                    continue

                # Examples:
                # "05.06.2026 (Freitag)"
                # "11.06.2026 (Donnerstag) 16:00 - 19:00 Uhr"
                date_text = date_text.split("(")[0].strip()

                try:
                    collection_date = datetime.strptime(
                        date_text,
                        "%d.%m.%Y",
                    ).date()
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
            raise ValueError(
                "Could not find any collection events."
            )

        # Remove duplicates
        unique_entries = {}
        for entry in entries:
            key = (entry.date, entry.type)
            unique_entries[key] = entry

        return sorted(
            unique_entries.values(),
            key=lambda x: x.date,
        )