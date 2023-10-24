from datetime import datetime

import bs4
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Adur & Worthing Councils"
DESCRIPTION = "Source for adur-worthing.gov.uk services for Adur & Worthing, UK."
URL = "https://adur-worthing.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "BN15 9UX", "address": "1 Western Road North"},
    "Test_002": {"postcode": "BN43 5WE", "address": "6 Hebe Road"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Refuse": "mdi:trash-can",
    "Garden": "mdi:leaf",
}


class Source:
    def __init__(self, postcode, address):
        self._postcode = postcode
        self._address = address

    def fetch(self):

        if self._postcode is None or self._address is None:
            raise ValueError("Either postcode or address is None")

        s = requests.Session()

        postcode_search_request = s.get(
            f"https://www.adur-worthing.gov.uk/bin-day/?brlu-address-postcode={self._postcode}&return-url=/bin-day/&action=search",
            headers=HEADERS,
        )
        html_addresses = postcode_search_request.content
        addresses = bs4.BeautifulSoup(html_addresses, "html.parser")
        addresses_select = addresses.find("select", {"id": "brlu-selected-address"})

        found_address = None
        for address in addresses_select.find_all("option"):
            if self._address in address.get_text():
                found_address = address

        if found_address is None:
            raise ValueError("Address not found")

        collections_request = s.get(
            f"https://www.adur-worthing.gov.uk/bin-day/?brlu-selected-address={address['value']}&return-url=/bin-day/",
            headers=HEADERS,
        )
        html_collections = collections_request.content
        bin_collections = bs4.BeautifulSoup(html_collections, "html.parser")

        bin_days_table = bin_collections.find("table", class_="bin-days")
        bin_days_table_body = bin_days_table.find("tbody")
        bin_days_by_type = bin_days_table_body.find_all("tr")

        entries = []

        for bin_by_type in bin_days_by_type:
            bin_type = bin_by_type.find("th").text
            icon = ICON_MAP.get(bin_type)
            bin_days = bin_by_type.find_all("td")[-1].get_text(separator="\n")
            for bin_day in bin_days.split("\n"):
                bin_datetime = datetime.strptime(bin_day, "%A %d %b %Y").date()
                entries.append(Collection(t=bin_type, date=bin_datetime, icon=icon))

        return entries
