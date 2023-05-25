import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Aberdeenshire Council"
DESCRIPTION = "Source for Aberdeenshire Council, UK."
URL = "https://aberdeenshire.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "000151124612"},
    "Test_002": {"uprn": "000151004105"},
    "Test_003": {"uprn": "0151035884"},
    "Test_004": {"uprn": 151170625}
}
ICON_MAP = {
    "Mixed recycling and food waste": "mdi:recycle",
    "Refuse and food waste": "mdi:trash-can",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        response = get_legacy_session().get(f"https://online.aberdeenshire.gov.uk/Apps/Waste-Collections/Routes/Route/{self._uprn}")
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        tr = soup.findAll("tr")
        for item in tr[1:]:  # Ignore table header row
            td = item.findAll("td")
            entries.append(
                Collection(
                    date=datetime.strptime(td[0].text.split(" ")[0], "%d/%m/%Y").date(),
                    t=td[1].text,
                    icon=ICON_MAP.get(td[1].text),
                )
            )

        return entries
