import logging
from datetime import date, datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Silkeborg Forsyning"
DESCRIPTION = "Silkeborg Forsyning"
URL = "https://www.silkeborgforsyning.dk/"
FORM_URL = "https://www.affaldonline.dk/kalender/silkeborg/"
API_URL = "https://www.affaldonline.dk/kalender/silkeborg/showInfo.php"

TEST_CASES = {
    "test": {
        "values": "A.C.Illums Vej|11||||8600|Silkeborg|45779561|1471144|0",
    },
}

_LOGGER = logging.getLogger("waste_collection_schedule.silkeborgforsyning_dk")

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

        # Extract waste collection information from the table
        table = soup.find('table')
        if not table:
            raise ValueError("No waste collection table found. Please check the provided values.")
        
        current_year = datetime.now().year
        current_month = datetime.now().month

        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                # Extract date and waste type
                date_str = cells[0].get_text(strip=True)
                waste_types = cells[1].get_text(strip=True)

                day, month = map(int, date_str.split('-'))
                
                # Determine the year based on the current month
                collection_year = current_year
                if month < current_month:
                    collection_year += 1

                collection_date = date(collection_year, month, day)

                for waste_type in waste_types.split(','):
                    entries.append(Collection(date=collection_date, t=waste_type.strip()))
                    _LOGGER.debug(
                        "Added collection: date=%s, type=%s",
                        collection_date,
                        waste_type.strip(),
                    )

        return entries
