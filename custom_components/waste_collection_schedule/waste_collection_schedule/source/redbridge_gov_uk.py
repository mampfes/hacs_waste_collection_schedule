from datetime import datetime
import requests
import re
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Redbridge Council"
DESCRIPTION = "Source for redbridge.gov.uk services for Redbridge Council, UK."
URL = "https://redbridge.gov.uk"
TEST_CASES = {
    "council office recycling only": {"uprn": 10034922090},
    "refuse and recycling only": {"uprn": 10013585215},
    "a church vicarage, garden, recycling, refuse": {"uprn": 10034912354}
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        r = requests.get(
            "https://my.redbridge.gov.uk/RecycleRefuse",
            params = {"uprn" : self._uprn}
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        services = soup.findAll("div", {"class": re.compile(".*CollectionDay")})

        entries = []

        for service in services:
            waste_type = service.find("h3").text

            month = service.find("div", {"class" : re.compile(".*-collection-month")}).text
            day = service.find("div", {"class" : re.compile(".*-collection-day-numeric")}).text
            year = datetime.now().year
            try:
                date = datetime.strptime('{day} {month} {year}'.format(day=day, month=month, year=year), "%d %B %Y")
            except:
                continue

            # if month is less than current month, year++
            if (date.month < datetime.now().month):
                date = datetime.strptime('{day} {month} {year}'.format(day=day, month=month, year=year+1), "%d %B %Y")

            entries.append(
                Collection(
                    date=date.date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.split(" ")[0].upper()),
                )
            )

        return entries
