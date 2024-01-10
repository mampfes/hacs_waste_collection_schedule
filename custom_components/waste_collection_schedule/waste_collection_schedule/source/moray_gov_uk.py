import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Moray Council"
DESCRIPTION = "Source for Moray Council, UK."
URL = "https://moray.gov.uk"
TEST_CASES = {
    "test_str": {"id": "00013734"},
    "test_int": {"id": 60216},
}
TEXT_MAP = {
    "images/green_bin.png": "Refuse (Green)",
    "images/brown_bin.png": "Garden and Kitchen Waste (Brown)",
    "images/purple_bin.png": "Cans and Plastic (Purple)",
    "images/blue_bin.png": "Paper and Card (Blue)",
    "images/orange_box_glass_bag.png": "Glass (Orange)",
}
ICON_MAP = {
    "images/green_bin.png": "mdi:trash-can",
    "images/brown_bin.png": "mdi:compost",
    "images/purple_bin.png": "mdi:recycle",
    "images/blue_bin.png": "mdi:newspaper-variant-multiple",
    "images/orange_box_glass_bag.png": "mdi:bottle-wine",
}


class Source:
    def __init__(self, id):
        self._id = str(id).zfill(8)

    def fetch(self):
        response = requests.Session().get(
            f"https://bindayfinder.moray.gov.uk/cal_2024_view.php?id={self._id}"
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        for month in soup.findAll("div", class_="cal_month_box"):
            parsed_date = None
            for div in month.findAll("div"):
                if "disp_day_area" in div["class"]:
                    parsed_date = datetime.strptime(div.text, "%a %d %B %Y").date()
                elif "disp_bins_cont" in div["class"]:
                    for i in div.findAll("img"):
                        entries.append(
                            Collection(
                                date=parsed_date,
                                t=TEXT_MAP.get(i["src"]),
                                icon=ICON_MAP.get(i["src"]),
                            )
                        )
        if not entries:
            _LOGGER.warning(f"No collection days found at {response.url}")
        return entries
