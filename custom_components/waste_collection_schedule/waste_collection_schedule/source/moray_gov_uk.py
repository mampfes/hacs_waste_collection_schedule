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
    "images/green_bin.png": "Green Refuse Bin",
    "images/brown_bin.png": "Brown Garden and Kitchen Waste Bin",
    "images/purple_bin.png": "Purple Cans and Plastic Bin",
    "images/blue_bin.png": "Blue Paper and Card Bin",
    "images/orange_box_glass_bag.png": "Glass Container",
}
ICON_MAP = {
    "images/green_bin.png": "mdi:trash-can",
    "images/brown_bin.png": "mdi:recycle",
    "images/purple_bin.png": "mdi:house",
    "images/blue_bin.png": "mdi:bulb",
    "images/orange_box_glass_bag.png": "mdi:glass",
}


class Source:
    def __init__(self, bin_id):
        self._bin_id = str(bin_id).zfill(8)

    def fetch(self):
        response = requests.Session().get(f"https://bindayfinder.moray.gov.uk/cal_2024_view.php?id={self._bin_id}")
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        for month in soup.findAll("div", class_='cal_month_box'):
            for div in month.findAll("div"):
                if 'disp_day_area' in div['class']:
                    parsed_date = datetime.strptime(div.text, "%a %d %B %Y").date()
                elif 'disp_bins_cont' in div['class']:
                    for i in div.findAll("img"):
                        entries.append(
                            Collection(
                                date=parsed_date,
                                t=TEXT_MAP.get(i['src']),
                                icon=ICON_MAP.get(i['src']),
                            )
                        )

        return entries
