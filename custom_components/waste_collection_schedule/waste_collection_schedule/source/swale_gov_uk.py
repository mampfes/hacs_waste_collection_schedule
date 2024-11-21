import json
import re

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Swale Borough Council"
DESCRIPTION = "Source for swale.gov.uk services for Swale, UK."
URL = "https://swale.gov.uk"
TEST_CASES = {
    "Swale House": {"uprn": 100062375927, "postcode": "ME10 3HT"},
    "1 Harrier Drive": {"uprn": 100061091726, "postcode": "ME10 4UY"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
}

API_URL = (
    "https://swale.gov.uk/bins-littering-and-the-environment/bins/my-collection-day"
)

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food-apple",
    "Garden": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode of the property",
    },
}

DATE_KEYS = {
    "NextDateUTC",
    "FollowingDateUTC",
    "Following2DateUTC",
    "Following3DateUTC",
}


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self) -> list[Collection]:
        entries = []

        session = requests.Session()
        session.headers.update(HEADERS)

        first_form_data = {
            "SQ_FORM_462397_PAGE": "1",
            "q462406:q1": self._postcode,
            "form_email_462397_submit": "Next &#10140;",
        }

        resp = session.post(API_URL, data=first_form_data)
        resp.raise_for_status()

        second_form_data = {
            "SQ_FORM_462397_PAGE": "2",
            "q462407:q3": self._uprn,
            "form_email_462397_submit": "Get Bin Days &#10140;",
        }

        collection_response = session.post(API_URL, data=second_form_data)
        collection_response.raise_for_status()

        collection_soup = BeautifulSoup(collection_response.text, "html.parser")

        section = collection_soup.find("section", id="SBC-YBD_main")
        if not section:
            raise ValueError(
                "Could not find SBC-YBD_main section. Most likely html has changed"
            )
        script = section.find("script", recursive=False)
        if not script:
            raise ValueError(
                "Could not find script entry. Most likely html has changed"
            )

        bin_data = re.search(
            r"var BIN_DAYS = Object\.entries\(JSON\.parse\('(.+)'\)\);", script.string
        )
        if not bin_data:
            raise ValueError(
                "Could not find BIN_DAYS in response. Most likely html has changed"
            )
        bin_days = json.loads(bin_data.group(1))
        for bin in bin_days:
            bin_details = bin_days[bin]
            if bin_details["Active"] == "Y":
                for dateKey in DATE_KEYS:
                    if dateKey in bin_details:
                        entries.append(
                            Collection(
                                date=parse(bin_details[dateKey]).date(),
                                t=bin,
                                icon=ICON_MAP.get(bin),
                            )
                        )
        if not entries:
            raise ValueError(
                "Could not get collections for the given combination of UPRN and Postcode."
            )
        return entries
