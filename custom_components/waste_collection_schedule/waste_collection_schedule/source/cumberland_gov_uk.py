from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Cumberland Council"
DESCRIPTION = "Source for cumberland.gov.uk services for Cumberland Council, UK."
URL = "https://cumberland.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "CA28 7QS", "uprn": "100110319463"},
    "Test_002": {"postcode": "CA28 8LG", "uprn": 100110320734},
    "Test_003": {"postcode": "CA28 6SW", "uprn": "10000895390"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Domestic Waste": "mdi:trash-can",
}
HEADERS = {"user-agent": "Mozilla/5.0"}
API_URLS = {
    "TOKEN": "https://waste.cumberland.gov.uk/renderform?t=25&k=E43CEB1FB59F859833EF2D52B16F3F4EBE1CAB6A",
    "SCHEDULE": "https://waste.cumberland.gov.uk/renderform/Form",
}


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = str(postcode).upper()
        self._uprn: str = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # Get token
        r = s.get(
            API_URLS["TOKEN"],
            headers=HEADERS,
        )

        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        token: str = soup.find("input", {"type": "hidden"}).get("value")

        # get schedule
        payload: dict = {
            "__RequestVerificationToken": token,
            "FF265": f"U{self._uprn}",
            "FF265-text": self._postcode,
            "FF265lbltxt": "Please select your address",
            "FormGuid": "371be01e-1204-428e-bccd-eeacaf7cbfac",
            "ObjectTemplateID": "25",
            "Trigger": "submit",
            "CurrentSectionID": "33",
            "TriggerCtl": "",
        }
        r = s.post(
            API_URLS["SCHEDULE"],
            headers=HEADERS,
            data=payload,
        )

        soup = BeautifulSoup(r.content, "html.parser")
        schedule: list = soup.find_all("div", {"class": "col"})
        schedule = [item.text for item in schedule[2:] if item.text != ""]
        waste_dates: list = schedule[0::2]
        waste_types: list = schedule[1::2]

        entries: list = []
        for i in range(0, len(waste_types)):
            entries.append(
                Collection(
                    date=datetime.strptime(waste_dates[i], "%A %d %B %Y").date(),
                    t=waste_types[i].replace(" Collection Service", ""),
                    icon=ICON_MAP.get(
                        waste_types[i].replace(" Collection Service", "")
                    ),
                )
            )

        return entries
