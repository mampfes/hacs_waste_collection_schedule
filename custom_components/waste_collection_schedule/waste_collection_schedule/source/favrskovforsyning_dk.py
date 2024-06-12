import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List
from datetime import date

from waste_collection_schedule import Collection

TITLE = "Favrskov Forsyning"
DESCRIPTION = "Favrskov Forsyning"
URL = "https://www.favrskovforsyning.dk/"
FORM_URL = "https://www.affaldonline.dk/kalender/favrskov/"
API_URL = "https://www.affaldonline.dk/kalender/favrskov/showInfo.php"

TEST_CASES = {
    "test": {
        "values": "Skovvej|20||||8382|Hinnerup|7484|109474|0",
    },
}

_LOGGER = logging.getLogger("waste_collection_schedule.affaldonline_dk")

DANISH_MONTHS = ["januar", "februar", "marts", "april", "maj", "juni", "juli", "august", "september", "oktober", "november", "december"]
DATE_REGEX = r"(\d{1,2})\. (\w+) (\d{4})"

class Source:
    def __init__(self, values: str):
        _LOGGER.debug("Initializing Source with values=%s", values)
        self._api_url = API_URL
        self._values = values

    def fetch(self) -> List[Collection]:
        _LOGGER.debug("Fetching data from %s", self._api_url)

        entries: List[Collection] = []

        post_data = {
            "values": self._values
        }
        
        response = requests.post(self._api_url, data=post_data)
        response.raise_for_status()

        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        waste_schemes = soup.find_all('strong')

        if not waste_schemes:
            raise ValueError("No waste schemes found. Please check the provided values.")

        for entry in waste_schemes:
            string = entry.next_sibling.next_sibling
            if string and 'Næste tømningsdag' in string:
                match = re.search(DATE_REGEX, string)
                if match:
                    try:
                        day = int(match.group(1))
                        month_name = match.group(2)
                        year = int(match.group(3))
                        month_index = DANISH_MONTHS.index(month_name) + 1
                        formatted_date = date(year, month_index, day)
                        waste_type = entry.get_text(strip=True)
                        entries.append(Collection(date=formatted_date, t=waste_type))
                        _LOGGER.debug("Added collection: date=%s, type=%s", formatted_date, waste_type)
                    except ValueError as e:
                        _LOGGER.error("Error parsing date: %s from string: %s", e, string)
                else:
                    _LOGGER.warning("No valid date found in string: %s", string)
        
        return entries
