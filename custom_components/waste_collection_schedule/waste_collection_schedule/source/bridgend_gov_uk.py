from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Bridgend County Borough Council"
DESCRIPTION = "Source for bridgend.gov.uk"
URL = "https://www.bridgend.gov.uk/"
TEST_CASES: dict = {
    "test_001": {"uprn": "100100479873"},
    "test_002": {"uprn": 10032996088},
    "test_003": {"uprn": "10090813443"},
}
ICON_MAP: dict = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}
HEADERS: dict = {"user-agent": "Mozilla/5.0"}

HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict = {
    "en": "an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}
PARAM_TRANSLATIONS: dict = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS: dict = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        r = s.get(
            f"https://bridgendportal.azurewebsites.net/property/{self._uprn}",
            headers=HEADERS,
        )
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")

        tds: list = soup.find_all("td", {"class": ["service-name", "next-service"]})
        waste_types: list = tds[0::2]
        waste_dates: list = tds[1::2]

        entries: list = []
        for i in range(len(waste_types)):
            waste_type = waste_types[i].text.split(" ")[0].replace("\n", "").strip()
            waste_date = (
                waste_dates[i]
                .text.split(" ")[1]
                .replace("\t", "")
                .replace("Service\n", "")
                .strip()
            )
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%d/%m/%Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
