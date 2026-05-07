import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "South Ribble Borough Council"
DESCRIPTION = (
    "Source for southribble.gov.uk services for South Ribble Borough Council, UK."
)
URL = "https://www.southribble.gov.uk"
COUNTRY = "gb"
TEST_CASES = {
    "South Ribble Borough Council, Civic Centre, W Paddock, Leyland PR25 1DH": {
        "postcode": "PR25 1DH",
        "uprn": "100012755948",
    },
}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food Waste": "mdi:food-apple",
    "Garden Waste": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://www.southribble.gov.uk/bincollectiondays "
        "and enter your postcode. Use browser dev tools to "
        "find the UPRN (the option value in the address dropdown)."
    ),
}

FORM_URL = "https://forms.chorleysouthribble.gov.uk/xfp/form/70"
FIELD_PREFIX = "qc576c657112a8277ba6f954ebc0490c946168363"
PAGE = "196"


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode.strip()
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            }
        )

        # Step 1: GET form and extract token
        r = session.get(FORM_URL, params={"page": PAGE, "locale": "en_GB"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {"name": "__token"}).attrs["value"]

        # Step 2: POST postcode
        data = {
            "__token": token,
            "page": PAGE,
            "locale": "en_GB",
            f"{FIELD_PREFIX}_0_0": self._postcode,
            "next": "Next",
        }
        r = session.post(FORM_URL, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {"name": "__token"}).attrs["value"]

        # Step 3: POST selected address
        data = {
            "__token": token,
            "page": PAGE,
            "locale": "en_GB",
            f"{FIELD_PREFIX}_0_0": self._postcode,
            f"{FIELD_PREFIX}_1_0": self._uprn,
            "next": "Next",
        }
        r = session.post(FORM_URL, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Step 4: Parse collection table
        entries = []
        for tr in soup.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if len(cells) < 2:
                continue

            service = cells[0].get_text(strip=True)
            date_text = cells[1].get_text(strip=True)

            # Normalise "Refuse Collection Service" -> "Refuse", "Food Waste Collection" -> "Food Waste"
            waste_type = re.sub(r" Collection(?: Service)?$", "", service).strip()

            try:
                collection_date = datetime.datetime.strptime(
                    date_text, "%d/%m/%y"
                ).date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
