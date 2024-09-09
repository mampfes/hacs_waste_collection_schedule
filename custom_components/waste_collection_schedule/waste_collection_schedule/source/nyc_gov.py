import requests
import urllib
from bs4 import BeautifulSoup
from dateutil.parser import parse

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "New York City"
DESCRIPTION = "Source for New York City, US."
URL = "https://www.nyc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": {"address": "120-55 Queens Blvd, Kew Gardens, NY 11424"},
    "Test_002": {"address": "1 W 72nd St, New York, NY 10023"},
}
ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Composting": "mdi:food",
    "Large items": "mdi:sofa",
}


class Source:
    def __init__(self, address):
        self._address = str(address)
        self._session = requests.Session()

    def fetch(self):
        url = f"https://dsnypublic.nyc.gov/dsny/api/geocoder/DSNYCollection?address={urllib.parse.quote(self._address)}"
        response = self._session.get(url)
        response.raise_for_status()
        data: dict = response.json()

        entries = []

        entries.extend(self.extract_collections(data['RegularCollectionSchedule'], 'Trash'))
        entries.extend(self.extract_collections(data['RecyclingCollectionSchedule'], 'Recycling'))
        entries.extend(self.extract_collections(data['OrganicsCollectionSchedule'], 'Composting'))
        entries.extend(self.extract_collections(data['BulkPickupCollectionSchedule'], 'Large items'))

        return entries


    def extract_collections(self, csvDays: str | None, waste_type: str) -> list[Collection]:
        """Given a string of days e.g. "Monday,Wednesday" return a list of Collection objects set to the given waste type"""
        if not csvDays:
            return []

        return [
            Collection(
                date=parse(day).date(),
                t=waste_type,
                icon=ICON_MAP.get(waste_type),
            )
            for day in csvDays.split(",")
        ]
