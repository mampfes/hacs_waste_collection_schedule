import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Moray Council"
DESCRIPTION = "Source for Moray Council, UK."
URL = "https://moray.gov.uk"
TEST_CASES = {
    "Test_001": {"bin_id": "00013734"},
    "Test_002": {"bin_id": "00060216"},
}
TEXT_MAP = {
    "G": "Green Refuse Bin",
    "B": "Brown Garden and Kitchen Waste Bin",
    "P": "Purple Cans and Plastic Bin",
    "C": "Blue Paper and Card Bin",
    "O": "Glass Container",
}
ICON_MAP = {
    "G": "mdi:trash-can",
    "B": "mdi:recycle",
    "P": "mdi:house",
    "C": "mdi:bulb",
    "O": "mdi:glass",
}


class Source:
    def __init__(self, bin_id):
        self._bin_id = str(bin_id).zfill(8)

    def fetch(self):
        response = requests.Session().get(f"https://bindayfinder.moray.gov.uk/cal_2024_view.php?id={self._bin_id}")
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        for month_container in soup.findAll("div", class_='month-container'):
            for div in month_container.findAll("div"):
                if 'month-header' in div['class']:
                    month = div.text
                elif div['class'] and div['class'][0] in ['B', 'GPOC', 'GBPOC']:
                    bins = div['class'][0]
                    dom = int(div.text)
                    parsed_date = datetime.strptime(f"{dom} {month} 2024", "%d %B %Y").date()
                    for i in bins:
                        entries.append(
                            Collection(
                                date=parsed_date,
                                t=TEXT_MAP.get(i),
                                icon=ICON_MAP.get(i),
                            )
                        )

        return entries
