import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wirral Council"
DESCRIPTION = "Source for wirral.gov.uk services for Wirral Council, UK."
URL = "https://wirral.gov.uk"
TEST_CASES = {
    "Test_001": {"street": "Vernon Avenue", "suburb": "Poulton"},
    "Test_002": {"street": "Vernon Avenue", "suburb": "Seacombe"},
    "Test_003": {"street": "Claremont Road", "suburb": "West Kirby"},
    "Test_004": {"street": "Beckenham Road", "suburb": "New Brighton"},
}
ICON_MAP = {
    "NON RECYCLEABLE (GREEN BIN)": "mdi:trash-can",
    "PAPER AND PACKAGING (GREY BIN)": "mdi:newspaper",
    "GARDEN WASTE (BROWN BIN)": "mdi:leaf",
}
WASTES = {
    "Non recycleable (green bin)",
    "Garden waste (brown bin)",
    "Paper and packaging (grey bin)",
}


class Source:
    def __init__(self, street, suburb):
        self._street = street
        self._suburb = suburb

    def fetch(self):
        s = requests.Session()
        #Loop through waste types
        entries = []
        for waste in WASTES:
            r = s.get(
                f"https://ww3.wirral.gov.uk//recycling/detailContentDru7.asp?s={self._street}&t={self._suburb}&c={waste}"
            )
            # extract dates
            soup = BeautifulSoup(r.text, "html.parser")
            dates = soup.findAll("li")
            if len(dates) != 0:
                for item in dates:
                    entries.append(
                        Collection(
                            date=datetime.strptime(item.text, "%d %B %Y").date(),
                            t=waste,
                            icon=ICON_MAP.get(waste.upper()),
                        )
                    )
        
        return entries
    