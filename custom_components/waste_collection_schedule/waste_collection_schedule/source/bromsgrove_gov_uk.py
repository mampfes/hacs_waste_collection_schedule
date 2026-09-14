from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Bromsgrove & Redditch Councils"
DESCRIPTION = "Source for the shared bin collection lookup used by Bromsgrove District Council and Redditch Borough Council, UK."
URL = "https://bromsgrove.gov.uk"
EXTRA_INFO = [
    {
        "title": "Redditch Borough Council",
        "url": "https://www.redditchbc.gov.uk",
        "default_params": {"council": "redditch"},
    },
]
TEST_CASES = {
    "Shakespeare House": {"uprn": "10094552413", "postcode": "B61 8DA"},
    "The Lodge": {"uprn": 10000218025, "postcode": "B60 2AA"},
    "Ceader Lodge": {"uprn": 100120576392, "postcode": "B60 2JS"},
    "Finstall Road": {"uprn": 100120571971, "postcode": "B60 3DE"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
}

# Bromsgrove District Council and Redditch Borough Council run a shared waste
# service and both publish the same "BinCollections" web app, one instance per
# council domain.
COUNCIL_DOMAINS = {
    "bromsgrove": "bincollections.bromsgrove.gov.uk",
    "redditch": "bincollections.redditchbc.gov.uk",
}

ICON_MAP = {
    "Grey": Icons.GENERAL_WASTE,
    "Green": Icons.RECYCLING,
    "Brown": Icons.ORGANIC,
}


class Source:
    def __init__(self, uprn: str, postcode: str, council: str = "bromsgrove"):
        self._uprn = uprn
        self._postcode = "".join(postcode.split()).upper()
        if council not in COUNCIL_DOMAINS:
            raise SourceArgumentNotFoundWithSuggestions(
                "council", council, COUNCIL_DOMAINS.keys()
            )
        self._domain = COUNCIL_DOMAINS[council]

    def fetch(self):
        entries: list[Collection] = []

        session = requests.Session()
        session.headers.update(HEADERS)

        form_data = {"UPRN": self._uprn}

        collection_response = session.post(
            f"https://{self._domain}/BinCollections/Details/", data=form_data
        )

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
