import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from datetime import datetime
from bs4 import BeautifulSoup
import re
import urllib3

# With verify=True the POST fails due to a SSLCertVerificationError.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "Rother District Council"
DESCRIPTION = "Source for Rother District Council."
URL = "https://www.rother.gov.uk"
TEST_CASES = {
    "Test_01": {"uprn": 10002653856},
    "Test_02": {"uprn": 100060102891},
}


ICON_MAP: dict[str, str] = {
    "refuse": "mdi:trash-can",
    "garden": "mdi:leaf",
    "recycling": "mdi:recycle",
}


API_URL = "https://www.rother.gov.uk/wp-admin/admin-ajax.php"


HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        data = {"action": "get_address_data", "uprn": self._uprn}

        r = requests.post(API_URL, headers=HEADERS, data=data, timeout=10, verify=False)
        r.raise_for_status()

        # Response is JSON with fields: success(boolean) and data (string containing HTML fragment)
        bin_collection_data = r.json()
        self.__validate_response(bin_collection_data)

        soup = BeautifulSoup(bin_collection_data["data"], "html.parser")

        entries = []
        for bin_type in ICON_MAP:
            date_span = soup.find("span", class_=f"find-my-nearest-bindays-{bin_type}")
            if date_span:
                date_str = date_span.text.strip()

                if date_str.startswith("Sign up"):
                    # Garden waste requires a subscription and may not be available for all
                    continue

                parsed_collection_date = datetime.strptime(
                    self.__remove_ordinal_indicators(date_str), "%A %d %B"
                )

                # The returned bin day does not include the year
                collection_year = self.__resolve_bin_collection_year(
                    parsed_collection_date.month
                )

                parsed_collection_date = parsed_collection_date.replace(
                    year=collection_year
                )

                icon = ICON_MAP.get(bin_type)
                entries.append(
                    Collection(
                        date=parsed_collection_date.date(), t=bin_type, icon=icon
                    )
                )

        if not entries:
            raise Exception("Unable to find any bin collection schedules")

        return entries

    def __validate_response(self, bin_collection_data):
        if "success" not in bin_collection_data or "data" not in bin_collection_data:
            raise Exception("Rother Disctrict Council returned an invalid response")

        if not bin_collection_data["success"]:
            raise Exception(
                "Rother Disctrict Council returned a non-successful response"
            )

    def __remove_ordinal_indicators(self, original_str: str) -> str:
        return re.sub(r"(\d)(st|nd|rd|th)", r"\1", original_str)

    def __resolve_bin_collection_year(self, collection_month: int) -> int:
        today = datetime.now()
        collection_year = today.year

        # Collection date is in previous year
        if collection_month == 12 and today.month == 1:
            collection_year -= 1

        # Collection date is in the next year
        elif collection_month == 1 and today.month == 12:
            collection_year += 1

        return collection_year
