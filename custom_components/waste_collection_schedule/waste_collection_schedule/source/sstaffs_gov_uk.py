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
        "uprn": "100031799974",
    },
}
ICON_MAP: dict = {
    "General waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden waste": "mdi:leaf",
    "Recycling & Garden waste": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict = {
    "en": "Your UPRN can be found by searching your postcode at https://www.sstaffs.gov.uk/viewyourcollectioncalendar and selecting your address. The objectId in the resulting URL is your UPRN. Alternatively, find your UPRN at https://www.findmyaddress.co.uk/",
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
            f"https://www.sstaffs.gov.uk/where-i-live?objectId={self._uprn}",
            headers=HEADERS,
        )
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")

        entries: list = []

        # get details on next bin collection
        next_date = soup.find("p", {"class": "collection-date"})
        next_bin = soup.find("p", {"class": "collection-type"})
        if next_date and next_bin:
            date_text = next_date.get_text(strip=True)
            type_text = next_bin.get_text(strip=True)
            entries.append(
                Collection(
                    date=datetime.strptime(date_text, "%A, %d %B %Y").date(),
                    t=type_text,
                    icon=ICON_MAP.get(type_text),
                )
            )

        # get details of future bin collections
        trs: list = soup.find_all("tr")
        for tr in trs[1:]:
            tds: list = tr.find_all("td")
            if len(tds) < 2:
                continue
            waste_type = tds[0].get_text(strip=True)
            waste_date = tds[1].get_text(strip=True)
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%A, %d %B %Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
