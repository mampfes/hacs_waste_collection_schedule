import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Cederbaum Braunschweig"
DESCRIPTION = "Cederbaum Braunschweig Paperimüll"
URL = "https://www.cederbaum.de"
TEST_CASES = {
    "Hans-Sommer-Str": {"street": "Hans-Sommer-Str."},
    "Adolfstr 31-42": {"street": "Adolfstr. 31-42"},
    "Am Schwarzen Berge": {"street": "am Schwarzen Berge "},
}

API_URL = "https://www.cederbaum.de/blaue-tonne/"
ICON_MAP = {
    "PAPER": "mdi:newspaper",
}

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
    }
}


class Source:
    def __init__(self, street):
        self._street = street

        self.page_source = None
        self.street_id = None
        self.collection_data = None

    def fetch_page_source(self):
        resp = requests.get(API_URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        self.page_source = soup

    def get_street_id(self):
        if not self.page_source:
            raise ValueError("No page source found")

        select = self.page_source.find("select")

        if not select:
            raise ValueError("No <select> tag found")

        options = select.find_all("option")
        for option in options:
            value = option.get("value")
            text = option.get_text()
            if text.lower().strip() == self._street.lower().strip():
                self.street_id = int(value)
                break

    def get_collection_data(self):
        if not self.page_source:
            raise ValueError("No page source found")

        script_tags = self.page_source.find_all("script")
        script_with_text = [tag for tag in script_tags if tag.string]
        pattern = re.compile(r"var rate = \[(.*?)\];")

        # the dates are stored in a hardcoded js array
        raw_date_text = None
        for script_tag in script_with_text:
            match = pattern.search(script_tag.string)
            if match:
                raw_date_text = match.group(1)
                break

        if not raw_date_text:
            raise ValueError("Raw date text not found")

        # one list of dates per location
        raw_dates = [text.strip('"') for text in raw_date_text.split('","')]
        self.collection_data = [dates.split(",") for dates in raw_dates]

    def fetch(self):
        self.fetch_page_source()
        self.get_street_id()
        self.get_collection_data()

        if not self.collection_data:
            raise ValueError("No collection data found")

        entries = []
        waste_dates = self.collection_data[self.street_id]  # type: ignore
        for waste_date in waste_dates:
            date = datetime.datetime.strptime(waste_date, "%d.%m.%Y")

            entries.append(
                Collection(
                    date=date.date(),
                    t="Paper",
                    icon=ICON_MAP.get("PAPER"),
                )
            )

        return entries
