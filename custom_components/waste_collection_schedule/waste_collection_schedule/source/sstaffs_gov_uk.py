from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "South Staffordshire Council"
DESCRIPTION = "Source for waste collection services for South Staffordshire Council"
URL = "https://sstaffs.gov.uk/"
HEADERS = {"user-agent": "Mozilla/5.0"}
TEST_CASES: dict = {
    "Test_001": {
        "uprn": "100031831923",
    },
    "Test_002": {
        "uprn": 100031811736,
    },
    "Test_003": {
        "uprn": "100031801746",
    },
}
ICON_MAP: dict = {
    "Grey Bin": "mdi:trash-can",
    "Green Bin and Blue Bin": "mdi:recycle",
    "Blue Bin and Grey Bin": "mdi:trash-can",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict = {
    "en": "Your uprn is displayed in the url when viewing your collection schedule. Alternatively, an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
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
            f"https://www.sstaffs.gov.uk/where-i-live?uprn={self._uprn}",
            headers=HEADERS,
        )
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")

        entries: list = []

        # get details on next bin collection
        next_bin = soup.find("p", {"class": "collection-type"})
        next_date = soup.find("p", {"class": "collection-date"})
        entries.append(
            Collection(
                date=datetime.strptime(next_date.text.strip(), "%A %d %B %Y").date(),
                t=next_bin.text.strip(),
                icon=ICON_MAP.get(next_bin.text.strip()),
            )
        )

        # get details of future bin collections
        trs: list = soup.find_all("tr")
        for tr in trs[1:]:
            tds: list = tr.find_all("td")
            waste_types: list = tds[0::2]
            waste_dates: list = tds[1::2]
            for i in range(len(waste_types)):
                waste_type: str = waste_types[i].text.strip()
                waste_date: str = waste_dates[i].text.strip()
                entries.append(
                    Collection(
                        date=datetime.strptime(waste_date, "%A %d %B %Y").date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
