import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wirral Council"
DESCRIPTION = "Source for wirral.gov.uk services for Wirral Council, UK."
URL = "https://wirral.gov.uk"
TEST_CASES = {
    "Test_001": {"street": "Vernon Avenue", "town": "Poulton"},
    "Test_002": {"street": "Vernon Avenue", "town": "Seacombe"},
    "Test_003": {"street": "Vernon Avenue", "town": "Poulton"},
    "Test_004": {"street": "Vernon Avenue", "town": "Seacombe"},
}
ICON_MAP = {
    "NON RECYCLABLE (GREEN BIN)": "mdi:trash-can",
    "PAPER AND PACKAGING (GREY BIN)": "mdi:newspaper",
    "GARDEN WASTE (BROWN BIN)": "mdi:leaf",
}
WASTES = {
    "Non recycleable (green bin)",
    "Garden waste (brown bin)",
    "Paper and packaging (grey bin)",
}


class Source:
    def __init__(self, street, town):
        self._street = street
        self._town = town

    def fetch(self):
        s = requests.Session()
        #Loop through waste types
        entries = []
        for waste in WASTES:
            r = s.get(
                f"https://ww3.wirral.gov.uk//recycling/detailContentDru7.asp?s={self._street}&t={self._town}&c={waste}"
            )
            # extract dates
            soup = BeautifulSoup(r.text, "html.parser")
            dates = soup.findAll("li")
            if dates != 0:
                for item in dates:
                    entries.append(
                        Collection(
                            date=datetime.strptime(item, "%d %m %Y").date(),
                            t=waste,
                            icon=ICON_MAP.get(waste.upper()),
                        )
                    )
        
        return entries
    