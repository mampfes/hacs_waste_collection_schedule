import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wirral Council"
DESCRIPTION = "Source for wirral.gov.uk services for Wirral Council, UK."
URL = "https://wirral.gov.uk"
TEST_CASES = {
    "Elm Avenue, Upton": {
        "postcode": "CH49 4NP",
        "address_value": "000042037487",
    },
}
ICON_MAP = {
    "Green bin": "mdi:trash-can",
    "Grey bin": "mdi:recycle",
    "Brown bin": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://www.wirral.gov.uk/bincal_dev/ and enter "
        "your postcode. Right-click on your address in the dropdown "
        "and select 'Inspect' to find the 12-digit option value. "
        "Use that as the address_value parameter."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your postcode, e.g. CH49 4NP.",
        "address_value": (
            "The 12-digit address value from the dropdown "
            "on the Wirral bin calendar page."
        ),
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address_value": "Address Value",
    }
}

BIN_URL = "https://www.wirral.gov.uk/bincal_dev/"
DATE_REGEX = r"(\w+ \d{1,2} \w+ \d{4})"


class Source:
    def __init__(self, postcode: str, address_value: str):
        self._postcode = postcode.strip()
        self._address_value = address_value.strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1: GET initial page
        r = session.get(BIN_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Collect form data
        data = self._extract_inputs(soup)
        data["ctl00$MainContent$Postcode"] = self._postcode
        data["ctl00$MainContent$LookupPostcode"] = "Look Up"

        # Step 2: POST postcode
        r = session.post(BIN_URL, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Step 3: Select address and find rounds
        data = self._extract_inputs(soup)
        data.pop("ctl00$MainContent$LookupPostcode", None)
        data["ctl00$MainContent$addressDropDown"] = self._address_value
        data["ctl00$MainContent$FindRounds"] = "Find collection rounds"

        r = session.post(BIN_URL, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Parse bin rows
        entries = []
        for row in soup.select("div.binRow"):
            h2 = row.find("h2")
            strong = row.find("strong")
            if not h2 or not strong:
                continue

            bin_type = h2.get_text(strip=True)
            date_text = strong.get_text(strip=True).rstrip(".")
            match = re.search(DATE_REGEX, date_text)
            if not match:
                continue

            entries.append(
                Collection(
                    date=datetime.strptime(match.group(1), "%A %d %B %Y").date(),
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries

    @staticmethod
    def _extract_inputs(soup: BeautifulSoup) -> dict:
        data = {}
        for inp in soup.find_all("input"):
            name = inp.get("name")
            if name:
                data[name] = inp.get("value", "")
        return data
