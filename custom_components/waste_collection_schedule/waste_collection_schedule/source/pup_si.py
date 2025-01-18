import requests
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "PUP Saubermacher"
DESCRIPTION = "Source for PUP Saubermacher."
URL = "https://www.pup-saubermacher.si/"
TEST_CASES = {
    "Sostanj 1": {"place_id": 412177},
    "Sostanj 2": {"place_id": 100911},
}

BIN_TYPES = {
    "M": "Mešani (črn)",
    "B": "Biološki (rjav)",
    "E": "Embalaža (rumeni)",
}
ICON_MAP = {
    "M": "mdi:trash-can",
    "B": "mdi:leaf",
    "E": "mdi:recycle",
}

BASE_URL = "https://www.pup-saubermacher.si/php/dobi_tabelo.php"


class Source:
    def __init__(self, place_id: int):
        self._place_id: int = place_id

    def fetch(self) -> list[Collection]:
        args = {
            "q": self._place_id,
        }
        response = requests.get(BASE_URL, params=args)
        response.encoding = 'utf-8'
        response.raise_for_status()

        content = BeautifulSoup(response.text, "html.parser")

        if response.text == "null" or not content.find_all("ul"):
            raise Exception("Invalid place id")

        entries = []
        data = self.parse_to_obj(content)

        for item in data:
            type_char = self.get_type(item["title"])

            for date_info in item["dates"]:
                date = self.get_date(date_info)

                if date is not None:
                    entries.append(Collection(date, BIN_TYPES[type_char], ICON_MAP[type_char]))

        return entries

    def parse_to_obj(self, content):
        # Find all <b> tags and their following <ul> tags
        b_tags = content.find_all('b')[2:]  # Skip the first two <b> tags
        data = []

        for b_tag in b_tags:
            title = b_tag.get_text()
            ul_tag = b_tag.find_next_sibling('ul')

            if ul_tag:
                dates = [line.strip() for line in ul_tag.decode_contents().split('<br>') if line.strip()]
                data.append({"title": title, "dates": dates[0].split("<br/>")})

        return data

    def get_type(self, title):
        if title.startswith("Mešana embalaža"):
            return "E"
        elif title.startswith("Mešani komunalni odpadki"):
            return "M"
        else:
            return "B"

    def get_date(self, date_info):
        parsed_date = date_info.split(" ")

        if isinstance(parsed_date, list) and len(parsed_date) == 1:
            return None
        else:
            date_obj = datetime.strptime(parsed_date[0].strip(), "%d.%m.%Y")
            return date_obj.date()