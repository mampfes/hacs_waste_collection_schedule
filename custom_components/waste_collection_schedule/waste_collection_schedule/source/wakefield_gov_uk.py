import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from bs4 import BeautifulSoup
import logging
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Wakefield UK"
DESCRIPTION = "Source for Wakefield UK."
URL = "https://www.wakefield.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "63077775"},
    #"Test_002": {"uprn": "63020035"},
    #"Test_003": {"uprn": "63109929"},
    #"Test_004": {"uprn": "63126706"},
}

ICON_MAP = {
    "Mixed recycling": "mdi:recycle",
    "Household waste": "mdi:trash-can",
    "Garden waste recycling": "mdi:leaf",
}

logging.basicConfig(level=logging.INFO)

API_URL = "https://www.wakefield.gov.uk/where-i-live/"

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        session = get_legacy_session()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:113.0) Gecko/20100101 Firefox/113.0"}
        session.headers.update(headers)
        
        r = session.get("https://www.wakefield.gov.uk/where-i-live/")
        r.raise_for_status()

        
        
        response = session.get(f"{URL}?uprn={self._uprn}&a=null")
        r.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []
        search = [
            "Mixed recycling",
            "Household waste",
            "Garden waste recycling"
        ]

        for item in search: 
            title = soup.find(item)
            logging.info(soup)
            # container = title.find_parent("div") // this was always null due to incapsula. Not sure what the solution is for this


        return entries
