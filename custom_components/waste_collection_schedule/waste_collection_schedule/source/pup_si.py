from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "PUP Saubermacher"
DESCRIPTION = "Source for PUP Saubermacher."
URL = "https://www.pup-saubermacher.si/"
TEST_CASES = {
    "Sostanj 1": {"place_id": 412177},
    "Sostanj 2": {"place_id": 100911},
}

BIN_TYPES = {
    "M": "Mesani",
    "B": "Bioloski",
    "E": "Embalaza",
}
ICON_MAP = {
    "M": Icons.GENERAL_WASTE,
    "B": Icons.ORGANIC,
    "E": Icons.RECYCLING,
}

# Headings used on the schedule page, mapped to the bin type they announce.
# The headings carry a suffix describing the bin colour, so they are matched
# by prefix.
WASTE_TYPE_PREFIXES = {
    "Mešana embalaža": "E",
    "Mešani komunalni odpadki": "M",
    "Biološki odpadki": "B",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your place_id (Odjemno mesto number) on your monthly PUP bill, or visit https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov",
}
PARAM_TRANSLATIONS = {
    "en": {
        "place_id": "Place ID (Odjemno mesto)",
    }
}

BASE_URL = "https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov"


class Source:
    def __init__(self, place_id: int):
        self._place_id: int = place_id

    def fetch(self) -> list[Collection]:
        args = {
            "q": self._place_id,
        }

        response = requests.get(BASE_URL, params=args)
        response.encoding = "utf-8"
        response.raise_for_status()

        content = BeautifulSoup(response.text, "html.parser")

        data = self.parse_to_obj(content)

        if not data:
            raise SourceArgumentNotFound("place_id", self._place_id)

        entries = []

        for item in data:
            type_char = item["type"]

            for date_info in item["dates"]:
                date = self.get_date(date_info)

                if date is not None:
                    entries.append(
                        Collection(date, BIN_TYPES[type_char], ICON_MAP[type_char])
                    )

        return entries

    def parse_to_obj(self, content):
        data = []

        for b_tag in content.find_all("b"):
            type_char = self.get_type(b_tag.get_text(strip=True))

            if type_char is None:
                continue

            ul_tag = b_tag.find_next("ul")

            if ul_tag:
                dates = [li.get_text(strip=True) for li in ul_tag.find_all("li")]
                data.append({"type": type_char, "dates": dates})

        return data

    def get_type(self, title):
        for prefix, type_char in WASTE_TYPE_PREFIXES.items():
            if title.startswith(prefix):
                return type_char
        return None

    def get_date(self, date_info):
        # List items look like "16.09.2026 sreda"; anything without a leading
        # date (e.g. an empty or explanatory entry) is skipped.
        date_str = date_info.split(" ")[0].strip()

        try:
            return datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            return None
