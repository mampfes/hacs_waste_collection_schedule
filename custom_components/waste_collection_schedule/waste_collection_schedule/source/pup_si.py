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

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your place_id (Odjemno mesto number) on your monthly PUP bill, or visit https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov",
}
PARAM_TRANSLATIONS = {
    "en": {
        "place_id": "Place ID (Odjemno mesto)",
    }
}

BASE_URL = (
    "https://www.pup-saubermacher.si/"
    "index.php/domov/urnik-odvoza-odpadkov"
)


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
            type_char = self.get_type(item["title"])
    
            for date_info in item["dates"]:
                date = self.get_date(date_info)
    
                if date is not None:
                    entries.append(
                        Collection(
                            date,
                            BIN_TYPES[type_char],
                            ICON_MAP[type_char],
                        )
                    )
    
        return entries

    def parse_to_obj(self, content):
        data = []
    
        waste_types = (
            "Mešana embalaža",
            "Mešani komunalni odpadki",
            "Biološki odpadki",
        )
    
        for b_tag in content.find_all("b"):
            title = b_tag.get_text(strip=True)
    
            if not title.startswith(waste_types):
                continue
    
            ul_tag = b_tag.find_next("ul")
    
            if ul_tag:
                dates = [
                    li.get_text(strip=True)
                    for li in ul_tag.find_all("li")
                ]
                data.append({"title": title, "dates": dates})
    
        return data

    def get_type(self, title):
        if title.startswith("Mešana embalaža"):
            return "E"
        if title.startswith("Mešani komunalni odpadki"):
            return "M"
        return "B"

    def get_date(self, date_info):
        parsed_date = date_info.split(" ")

        if isinstance(parsed_date, list) and len(parsed_date) == 1:
            return None
        date_obj = datetime.strptime(parsed_date[0].strip(), "%d.%m.%Y")
        return date_obj.date()
