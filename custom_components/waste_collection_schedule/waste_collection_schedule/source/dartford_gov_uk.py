from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Dartford Borough Council"
DESCRIPTION = "Source for Dartford Borough Council."
URL = "https://dartford.gov.uk"
TEST_CASES: dict = {
    "Test_001": {"uprn": "100060862889"},
    "Test_002": {"uprn": 100060857499},
    "Test_003": {"uprn": "200000540020"},
}
HEADERS: dict = {"user-agent": "Mozilla/5.0"}
ICON_MAP: dict = {
    "RECYCLING": "mdi:recycle",
    "REFUSE": "mdi:trash-can",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict = {
    "en": "Your UPRN is displayed in the top left corner of the Dartford website when you are viewing your collection schedule. Alternatively, you can discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
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
        self._uprn: str = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        r = s.get(
            f"https://windmz.dartford.gov.uk/ufs/WS_CHECK_COLLECTIONS.eb?UPRN={self._uprn}",
            headers=HEADERS,
        )

        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        waste_types: list = soup.find_all(
            "td", {"data-eb-colheader": "Collection Type"}
        )
        waste_dates: list = soup.find_all("td", {"data-eb-colheader": "Date"})

        entries: list = []
        for i in range(len(waste_types)):
            waste_type: str = waste_types[i].text.strip()
            waste_date: str = waste_dates[i].text.strip()
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%d/%m/%Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
