import datetime
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "Hastings District Council"
DESCRIPTION = "Source for Napier City Council"
URL = "https://www.hastingsdc.govt.nz/"
COUNTRY = "nz"
API_URL = "https://data.napier.govt.nz/regional/hdc/widgets/collectiondays/do_collectiondays.php"
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}
HEADERS = {"User-Agent": "Mozilla/5.0"}

TEST_CASES = {
    "Test1": {"address": "200 Heretaunga Street East"},
    "Test2": {"address": "805 Fitzroy Avenue"},
    "Test3": {"address": "704 Park Road South"},
    "Test4": {"address": "21 Drovers Way"},
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch_property_details(self):
        params = {
            "search": self._address,
            "council": "hdc",
            "type": "address",
        }
        try:
            response = requests.get(
                "https://data.napier.govt.nz/regional/shared/widgets/propertysearch/do_search.php",
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                raise ValueError(f"Failed to locate address: {self._address}")

            # Check if the response indicates no record was found
            if data[0].get("id") == "0" and "No record found for your search" in data[
                0
            ].get("value", ""):
                raise ValueError(f"No record found for address: {self._address}")

            # Check if there is more than one result
            if len(data) > 1:
                raise ValueError(
                    f"Multiple results found for address: {self._address}. Must be a single address only."
                )

            # Check if the expected keys exist in the first item of the data list
            if (
                "valuation_id" not in data[0]
                or "sufi_id" not in data[0]
                or "ra_unique_id" not in data[0]
            ):
                raise ValueError(f"Expected keys not found in the response: {data[0]}")

            valuation_id = data[0]["valuation_id"]
            sufi_id = data[0]["sufi_id"]
            ra_unique_id = data[0]["ra_unique_id"]

            return valuation_id, sufi_id, ra_unique_id

        except Exception as e:
            raise ValueError(
                f"Failed while locating address: {self._address} with error: {e}"
            )

    def fetch(self):
        v, s, r = self.fetch_property_details()

        params = {
            "v": v,
            "s": s,
            "r": r,
        }
        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ValueError(f"API request failed: {e}")

        if not data.get("success", False):
            raise ValueError("API response indicates failure.")

        html_content = data.get("html", "")
        if not html_content:
            _LOGGER.warning("No HTML content found in API response.")
            raise ValueError("No HTML content in API response.")

        soup = BeautifulSoup(html_content, "html.parser")
        entries = []

        tables = soup.find_all("table")
        for table in tables:
            th = table.find("th")
            if not th:
                _LOGGER.warning("No th element found in table.")
                continue

            collection_type = th.get_text(strip=True).replace(" collection", "")

            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if not cells:
                    continue

                collection_info = cells[0].get_text(strip=True)
                if "Every" in collection_info:
                    days = collection_info.split(". ")[0].split("/")  # Extract the days
                    for day in days:
                        # Calculate the weekday index of the target day
                        target_weekday = datetime.datetime.strptime(day, "%A").weekday()

                        today = datetime.date.today()

                        # Find the current week's occurrence of the target day
                        today_weekday = today.weekday()
                        days_until_next_occurrence = (
                            target_weekday - today_weekday + 7
                        ) % 7

                        # Get the date of the next occurrence
                        next_occurrence = today + datetime.timedelta(
                            days=days_until_next_occurrence
                        )

                        # Get the past 7 and next 7 occurrences
                        for i in range(-7, 8):  # From -7 to 7 inclusive
                            occurrence_date = next_occurrence + datetime.timedelta(
                                weeks=i
                            )

                            # Keep the date as datetime.date
                            collection_date = occurrence_date

                            entries.append(
                                Collection(
                                    date=collection_date,
                                    t=collection_type.capitalize(),
                                    icon=ICON_MAP.get(
                                        collection_type.capitalize(), "mdi:calendar"
                                    ),
                                )
                            )

        if not entries:
            raise ValueError(
                f"No collection entries found for address: {self._address}"
            )

        return entries
