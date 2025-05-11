from datetime import datetime, timedelta

import bs4
import requests
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Adur & Worthing Councils"
DESCRIPTION = "Source for adur-worthing.gov.uk services for Adur & Worthing, UK."
URL = "https://adur-worthing.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "BN15 9UX", "address": "1 Western Road North"},
    "Test_002": {"postcode": "BN43 5WE", "address": "6 Hebe Road"},
    "Test_003": {"uprn": "100062209109"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Refuse": "mdi:trash-can",
    "Garden": "mdi:leaf",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
    }
}


class Source:
    def __init__(self, postcode=None, address=None, uprn=None):
        if uprn is not None:
            self._uprn = uprn
            self._postcode = None
            self._address = None
        else:
            self._postcode = postcode
            self._address = address
            self._uprn = None

    def fetch(self):
        s = requests.Session()

        if self._uprn is not None:
            r = s.get(
                f"https://www.adur-worthing.gov.uk/bin-day/?brlu-selected-address={self._uprn}",
                headers=HEADERS,
            )
            html_collections = r.content
        else:
            if self._postcode is None or self._address is None:
                raise SourceArgumentExceptionMultiple(
                    ["postcode", "address"],
                    "either postcode or address needs to be provided but neither was",
                )

            postcode_search_request = s.get(
                f"https://www.adur-worthing.gov.uk/bin-day/?brlu-address-postcode={self._postcode}&return-url=/bin-day/&action=search",
                headers=HEADERS,
            )
            html_addresses = postcode_search_request.content
            addresses = bs4.BeautifulSoup(html_addresses, "html.parser")
            addresses_select = addresses.find("select", {"id": "brlu-selected-address"})

            found_address = None
            for address in addresses_select.find_all("option"):
                if self._address.upper() in address.get_text().upper():
                    found_address = address

            if found_address is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "address",
                    self._address,
                    [a.get_text() for a in addresses_select.find_all("option")],
                )

            collections_request = s.get(
                f"https://www.adur-worthing.gov.uk/bin-day/?brlu-selected-address={found_address['value']}&return-url=/bin-day/",
                headers=HEADERS,
            )
            html_collections = collections_request.content

        bin_collections = bs4.BeautifulSoup(html_collections, "html.parser")
        containers = bin_collections.find_all(
            "div", {"class": "bin-collection-listing-row row"}
        )

        entries = []

        for container in containers:
            waste_type = container.find("h2").text
            waste_texts = container.find_all("p")
            for text in waste_texts:
                if "Next collection:" in text.text:
                    waste_date = text.text.split(": ")[1]
            # Append year and deal with year-end dates
            waste_date += f" {datetime.now().year}"
            waste_date = parser.parse(waste_date).date()
            if waste_date.month < datetime.now().month:
                waste_date = waste_date + timedelta(days=365)
            # waste descriptions changed, so make consistent with old configs
            if waste_type == "General rubbish":
                waste_type = "Refuse"
            if waste_type == "Garden waste":
                waste_type = "Garden"

            entries.append(
                Collection(t=waste_type, date=waste_date, icon=ICON_MAP.get(waste_type))
            )

        return entries
