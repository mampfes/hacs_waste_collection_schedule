from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bromsgrove City Council"
DESCRIPTION = "Source for bromsgrove.gov.uk services for Bromsgrove, UK."
URL = "https://bromsgrove.gov.uk"
TEST_CASES = {
    "Shakespeare House": {"uprn": "10094552413", "postcode": "B61 8DA"},
    "The Lodge": {"uprn": 10000218025, "postcode": "B60 2AA"},
    "Ceader Lodge": {"uprn": 100120576392, "postcode": "B60 2JS"},
    "Finstall Road": {"uprn": 100120571971, "postcode": "B60 3DE"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
}

API_URLS = {
    "collection": "https://bincollections.bromsgrove.gov.uk/BinCollections/Details/",
}
ICON_MAP = {
    "Grey": "mdi:trash-can",
    "Green": "mdi:recycle",
    "Brown": "mdi:leaf",
}


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = "".join(postcode.split()).upper()

    def fetch(self):
        entries: list[Collection] = []

        session = requests.Session()
        session.headers.update(HEADERS)

        form_data = {"UPRN": self._uprn}

        collection_response = session.post(API_URLS["collection"], data=form_data)

        # Parse HTML
        soup = BeautifulSoup(collection_response.text, "html.parser")

        # Find postcode
        postcode = "".join(soup.find("h3").text.split()[-2:]).upper()

        # Find bins and their collection details
        bins = soup.find_all(class_="collection-container")

        # Initialize lists to store extracted information
        bin_info = []

        # Extract information for each bin
        for bin in bins:
            bin_name = bin.find(class_="heading").text.strip()
            bin_color = bin.find("img")["alt"]
            collection_dates = []
            collection_details = bin.find_all(class_="caption")
            for detail in collection_details:
                date_string = detail.text.split()[-3:]
                collection_date = " ".join(date_string)
                collection_dates.append(
                    datetime.strptime(collection_date, "%d %B %Y").date()
                )
            bin_info.append(
                {
                    "Bin Name": bin_name,
                    "Bin Color": bin_color,
                    "Collection Dates": collection_dates,
                }
            )

        # Check if the postcode matches the one provided, otherwise don't fill in the output
        if postcode == self._postcode:
            for info in bin_info:
                entries.append(
                    Collection(
                        date=info["Collection Dates"][0],
                        t=info["Bin Name"],
                        icon=ICON_MAP.get(info["Bin Color"], "mdi:help"),
                    )
                )

        if not entries:
            raise ValueError(
                "Could not get collections for the given combination of UPRN and Postcode."
            )

        return entries
