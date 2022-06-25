import logging
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "fccenvironment.co.uk"

DESCRIPTION = (
    """Consolidated source for waste collection services for ~60 local authorities.
        Currently supports:
        Market Harborough
        """
)

URL = "https://fccenvironment.co.uk"

TEST_CASES = {
    "Test_001" : {"uprn": "100030491624"},
    "Test_002": {"uprn": "100030491614"},
    "Test_003": {"uprn": "100030493289"},
    "Test_004": {"uprn": "200001136341"}
}


ICONS = {
    "NON-RECYCLABLE WASTE BIN COLLECTION": "mdi:trash-can",
    "RECYCLING COLLECTION": "mdi:recycle",
    "GARDEN WASTE COLLECTION": "mdi:leaf",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = uprn

    def fetch(self):

        s = requests.Session()

        if self._uprn:
            # POST request returns schedule for matching uprn
            payload = {
                "Uprn": self._uprn
            }
            r = s.post("https://www.fccenvironment.co.uk/harborough/detail-address", data = payload)
            responseContent = r.text

        entries = []
        # Extract waste types and dates from responseContent
        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find("div", attrs={"class": "blocks block-your-next-scheduled-bin-collection-days"})
        items = services.find_all("li")
        for item in items:
            date_text = item.find("span", attrs={"class": "pull-right"}).text.strip()
            try:
                date = datetime.strptime(date_text, "%d %B %Y").date()
            except ValueError:
                continue
            else:
                waste_type = item.text.split(' (')[0]
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=ICONS.get(waste_type.upper()),    
                    )
                )

        return entries
