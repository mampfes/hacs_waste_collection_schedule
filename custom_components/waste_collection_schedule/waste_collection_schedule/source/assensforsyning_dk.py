import logging
import re
from datetime import date
from typing import List

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Assens Forsyning"
DESCRIPTION = "Assens Forsyning"
URL = "https://www.assensforsyning.dk/"
FORM_URL = "https://www.affaldonline.dk/kalender/assens/"
API_URL = "https://www.affaldonline.dk/kalender/assens/showInfo.php"

TEST_CASES = {
    "test": {
        "values": "Rådhus Allé|1||||5610|Assens|12544|607551|0",
    },
}

_LOGGER = logging.getLogger("waste_collection_schedule.assensforsyning_dk")

DANISH_MONTHS = [
    "januar",
    "februar",
    "marts",
    "april",
    "maj",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "december",
]
DATE_REGEX = r"(\d{1,2})\. (\w+) (\d{4})"

class Source:
    def __init__(self, values: str):
        _LOGGER.debug("Initializing Source with values=%s", values)
        self._api_url = API_URL
        self._values = values

    def fetch(self) -> List[Collection]:
        _LOGGER.debug("Fetching data from %s", self._api_url)

        entries: List[Collection] = []

        post_data = {"values": self._values}

        response = requests.post(self._api_url, data=post_data)
        response.raise_for_status()

        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all instances of "Næste tømningsdag"
        next_pickup_info = soup.find_all(string=re.compile("Næste tømningsdag:"))
        if not next_pickup_info:
            raise ValueError("No waste schemes found. Please check the provided values.")

        for info in next_pickup_info:
            text = info.strip()
            match = re.search(DATE_REGEX, text)
            if match:
                try:
                    day = int(match.group(1))
                    month_name = match.group(2)
                    year = int(match.group(3))
                    month_index = DANISH_MONTHS.index(month_name) + 1
                    formatted_date = date(year, month_index, day)

                    # Extract waste type from the text
                    waste_type = re.search(r"\((.*?)\)", text).group(1)

                    entries.append(Collection(date=formatted_date, t=waste_type))
                    _LOGGER.debug(
                        "Added collection: date=%s, type=%s",
                        formatted_date,
                        waste_type,
                    )
                except ValueError as e:
                    _LOGGER.error(
                        "Error parsing date: %s from string: %s", e, text
                    )
            else:
                _LOGGER.warning("No valid date found in string: %s", text)

        return entries
