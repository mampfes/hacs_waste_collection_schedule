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
    "Test_004": {"uprn": 10000895390},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Refuse": "mdi:trash-can",
    "Paper": "mdi:newspaper",
}
HEADERS = {"user-agent": "Mozilla/5.0"}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}
PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode of your property",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Postcode of your property",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


class Source:
    def __init__(
        self,
        uprn: str | int,
        postcode: str | None = None,
    ):
        # postcode is no longer needed, provide default value to make it optional for newer configs
        self._uprn: str = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        r = s.get(
            f"https://www.cumberland.gov.uk/bins-recycling-and-street-cleaning/waste-collections/bin-collection-schedule/view/{self._uprn}",
            headers=HEADERS,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "lxml")

        entries = []
        for item in soup.select("li.waste-collection__day"):
            waste_date = item.select_one("time")["datetime"]
            waste_type = item.select_one(".waste-collection__day--colour").get_text(
                strip=True
            )
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%Y-%m-%d").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
