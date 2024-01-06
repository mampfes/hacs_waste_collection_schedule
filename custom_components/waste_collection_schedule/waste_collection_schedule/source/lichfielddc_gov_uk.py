import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Lichfield District Council"
DESCRIPTION = "Source for Lichfield District Council, UK."
URL = "https://lichfielddc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100031695248"},
    "Test_002": {"uprn": "100031704571"},
    "Test_003": {"uprn": "10002768095"},
    "Test_004": {"uprn": "100031699855"},
}
ICON_MAP = {
    "Black Bin": "mdi:trash-can",
    "Blue Bin": "mdi:recycle",
    "Blue Sack": "mdi:recycle",
    "Purple Bin": "mdi:recycle",
    "Garden Bin": "mdi:leaf",
    "Brown Bin": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        response = requests.get(
            "https://www.lichfielddc.gov.uk/bincalendar", params={"uprn": self._uprn}
        )
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        bins = soup.find_all("h3", class_="bin-collection-tasks__heading")
        dates = soup.find_all("p", class_="bin-collection-tasks__date")

        for i in range(len(dates)):
            bint = " ".join(bins[i].text.split()[2:4])
            date = parser.parse(dates[i].text).date()
            entries.append(
                Collection(
                    date=date,
                    t=bint,
                    icon=ICON_MAP.get(bint),
                )
            )

        return entries
