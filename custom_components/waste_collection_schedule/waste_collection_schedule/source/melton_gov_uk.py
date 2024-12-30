from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Melton Borough Council"
DESCRIPTION = "Source for waste collection services for Melton Borough Council, UK"
URL = "https://www.melton.gov.uk/"

HEADERS = {"user-agent": "Mozilla/5.0"}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

TEST_CASES = {
    "Test_001": {
        "uprn": "100030544791",
    },
    # "Test_002": {
    #     "uprn": 100090883974,
    # },
    # "Test_003": {
    #     "uprn": "100090880632",
    # },
}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        params: dict = {
            "id": self._uprn,
            "redirect": "collections",
            "rememberloc": "",
        }
        r = s.get(
            "https://my.melton.gov.uk/set-location", headers=HEADERS, params=params
        )
        r.raise_for_status
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")

        entries: list = []
        list_items: list = soup.find_all("li", {"class": ["dark-blue", "burgundy"]})
        for item in list_items:
            waste_type: str = item.find("h2").text
            waste_dates: list = item.find("strong").text.split(", and then ")
            for waste_date in waste_dates:
                entries.append(
                    Collection(
                        date=datetime.strptime(waste_date, "%d/%m/%Y").date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
