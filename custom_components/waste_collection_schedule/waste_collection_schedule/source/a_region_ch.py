import datetime
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "A-Region"
DESCRIPTION = "Source for A-Region, Switzerland waste collection."
URL = "https://www.a-region.ch"
TEST_CASES = {
    "Andwil": {"municipality": "Andwil"},
}

BASE_URL = "https://www.a-region.ch"


class Source:
    def __init__(self, municipality):
        self._municipality = municipality

    def fetch(self):
        municipalities = self.get_municipalities()
        if self._municipality not in municipalities:
            raise Exception(f"municipality '{self._municipality}' not found")

        waste_types = self.get_waste_types(municipalities[self._municipality])

        entries = []

        for (waste_type, link) in waste_types.items():
            dates = self.get_dates(link)

            for d in dates:
                entries.append(Collection(d, waste_type))

        return entries

    def get_municipalities(self):
        r = requests.get(f"{BASE_URL}/index.php?apid=13875680&apparentid=4618613")
        r.raise_for_status()

        municipalities = {}

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/index.hp"
            href = download.get("href")
            if "ref=search" in href:
                for title in download.find_all("div", class_="title"):
                    # title ::= "Abfallkalender Andwil"
                    municipalities[title.string.removeprefix("Abfallkalender ")] = href

        return municipalities

    def get_waste_types(self, link):
        r = requests.get(f"{BASE_URL}{link}")
        r.raise_for_status()

        waste_types = {}

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/index.php?apid=12731252&amp;apparentid=5011362"
            href = download.get("href")
            if "apparentid" in href:
                for title in download.find_all("div", class_="title"):
                    # title ::= "Altmetall"
                    waste_types[title.string] = href

        return waste_types

    def get_dates(self, link):
        r = requests.get(f"{BASE_URL}{link}")
        r.raise_for_status()

        dates = set()

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        for download in downloads:
            # href ::= "/appl/ics.php?apid=12731252&amp;from=2022-05-04%2013%3A00%3A00&amp;to=2022-05-04%2013%3A00%3A00"
            href = download.get("href")
            if "ics.php" in href:
                parsed = urlparse(href)
                query = parse_qs(parsed.query)
                date = datetime.datetime.strptime(query["from"][0], "%Y-%m-%d %H:%M:%S")
                dates.add(date.date())

        return dates
