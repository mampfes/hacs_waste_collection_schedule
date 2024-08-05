from datetime import datetime
from typing import List

import bs4
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Arun District Council"
DESCRIPTION = "Source for arun.gov.uk services for Arun District, UK."
URL = "https://www.arun.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "BN17 5JA", "address": "21A Beach Road, Littlehampton"},
    "Test_002": {"postcode": "BN16 1AA", "address": "2 Downs Way, East Preston"}
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can"
}


class Source:
    def __init__(self, postcode, address):
        self._postcode = postcode
        self._address = address

    def _get_gds_error(self, soup: bs4.BeautifulSoup) -> str:
        return soup.find("div", {"class": "govuk-error-summary__body"}).get_text(strip=True)

    def fetch(self) -> List[Collection]:
        if self._postcode is None or self._address is None:
            raise ValueError("Either postcode or address is None")

        s = requests.Session()
        s.headers = HEADERS

        try:
            for url in ("https://www1.arun.gov.uk/when-are-my-bins-collected", "https://www1.arun.gov.uk/when-are-my-bins-collected/postcode"):
                start_session = s.get(url)
                start_session.raise_for_status()
        except requests.HTTPError as e:
            raise Exception("Failed to start session") from e

        try:
            postcode_search_request = s.post(
                f"https://www1.arun.gov.uk/when-are-my-bins-collected/postcode",
                data={"postcode": self._postcode}
            )
            postcode_search_request.raise_for_status()
        except requests.HTTPError as e:
            raise Exception("Failed to search postcode") from e

        addresses = bs4.BeautifulSoup(
            postcode_search_request.content, "html.parser")

        addresses_select = addresses.find(
            "select", {"id": "address"})
        if addresses_select is None:
            try:
                error_summary = self._get_gds_error(addresses)
            except (AttributeError, Exception) as e:
                raise Exception(
                    "An unexpected error occurred while fetching addresses") from e
            raise ValueError(error_summary)

        options = addresses_select.find_all("option")[1:]
        try:
            found_address = next((address for address in options if self._address.upper(
            ) in address.get_text().upper()))
        except StopIteration as e:
            raise ValueError(
                f"Address not found. Searched for {self._address} but, should be one of {[a.get_text() for a in options]}"
            ) from e

        try:
            collections_request = s.post(
                f"https://www1.arun.gov.uk/when-are-my-bins-collected/select",
                data={"address": found_address.get("value")}
            )
            collections_request.raise_for_status()
        except requests.HTTPError as e:
            raise Exception("Failed to fetch collections for address") from e

        bin_collections = bs4.BeautifulSoup(
            collections_request.content, "html.parser")

        try:
            bin_days_main = bin_collections.find(
                "main", {"id": "main-content"})
            bin_days_table = bin_days_main.find("table")
            bin_days_table_body = bin_days_table.find("tbody")
            bin_days_by_type = bin_days_table_body.find_all("tr")

            entries = []
            for bin_by_type in bin_days_by_type:
                bin_type = bin_by_type.find("th").text.split(" ")[0]
                icon = ICON_MAP.get(bin_type)
                bin_date = bin_by_type.find_all(
                    "td")[0].get_text()  # DD/MM/YYYY
                bin_datetime = datetime.strptime(bin_date, "%d/%m/%Y").date()
                entries.append(Collection(
                    t=bin_type, date=bin_datetime, icon=icon))
        except Exception as e:
            raise Exception("Failed to parse bin collection table") from e

        return entries
