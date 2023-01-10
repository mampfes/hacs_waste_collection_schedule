import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaftsbetrieb Esslingen"
DESCRIPTION = "Source for AWB Esslingen, Germany"
URL = "https://www.awb-es.de"

TEST_CASES = {
    "Aichwald": {"city": "Aichwald", "street": "Alte Dorfstrasse"},
    "Kohlberg": {"city": "Kohlberg", "street": "alle Straßen"},
}

HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(self, city, street=None):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        params = {
            "city": self._city,
            "street": self._street,
            "direct": "true",
        }
        r = session.get(
            "https://www.awb-es.de/abfuhr/abfuhrtermine/__Abfuhrtermine.html",
            params=params,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        ics_urls = list()
        for download in downloads:
            href = download.get("href")
            if "t=ics" in href and href not in ics_urls: #The website lists the same url multiple times, we only want it once
                ics_urls.append(href)

        if not ics_urls:
            raise Exception(f"ics url not found")

        entries = []
        for ics_url in ics_urls:
            # get ics file
            r = session.get(ics_url, headers=HEADERS)
            r.raise_for_status()

            # parse ics file
            dates = self._ics.convert(r.text)

            for d in dates:
                entries.append(Collection(d[0], d[1]))
        
        return entries
