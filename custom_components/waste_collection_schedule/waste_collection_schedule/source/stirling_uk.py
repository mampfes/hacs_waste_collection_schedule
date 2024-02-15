from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stirling.gov.uk"
DESCRIPTION = "Personally maintained Source for  stirling.gov.uk services for the city of Stirling, UK."
URL = "https://stirling.gov.uk"
TEST_CASES = {
    "Kildean Road": {"route": "9748"},
}

ICONS = {
    "Grey Bin": "mdi:trash-can",
    "Blue Bin": "mdi:bottle-soda",
    "Brown Bin": "mdi:food-off",
    "Green Bin": "mdi:recycle",
    "Glass Bin": "mdi:bottle-wine",
}

REM_STRING1 = "Then every"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/",
    "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Sec-Gpc": "1",
    "Upgrade-Insecure-Requests": "1",
}


class Source:
    def __init__(self, route: str | int):
        self._route = route

    def fetch(self):
        # get json file
        URL = f"https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/collections/?route={self._route}"

        page = requests.get(URL, headers=headers)

        soup = BeautifulSoup(page.content, "html.parser")

        scheduleItems = soup.find_all("li", class_="schedule__item")

        entries = []

        # extract data from json

        for item in scheduleItems:
            BinType = item.find("h2", class_="schedule__title")
            NextCollection = item.find("p", class_="schedule__summary")
            # bin_type_text = BinType.text.strip()
            # next_collection_text = NextCollection.text.strip().split(REM_STRING1, 1)[0].strip()
            # date_object = datetime.strptime(next_collection_text, "%A %d %b %Y")
            # next_collection_text = date_object.date()
            entries.append(
                Collection(
                    # date=next_collection_text,
                    # t=bin_type_text,
                    # icon=ICONS[bin_type_text],
                    date=datetime.strptime(
                        NextCollection.text.strip().split(REM_STRING1, 1)[0].strip(),
                        "%A %d %b %Y",
                    ).date(),
                    t=BinType.text.strip(),
                    icon=ICONS[BinType.text.strip()],
                )
            )

        return entries
