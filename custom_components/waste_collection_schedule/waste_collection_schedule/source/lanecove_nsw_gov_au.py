import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Lane Cove Council"
DESCRIPTION = "Source for Lane Cove Council rubbish collection."
URL = "https://www.lanecove.nsw.gov.au/"

TEST_CASES = {
    "17 Moore ST": {"address": "17 Moore ST LANE COVE WEST, 2066"},
    "1 Austin St": {"address": "1 Austin ST LANE COVE, 2066"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Food Waste": "mdi:food-apple",
    "Green Waste": "mdi:leaf",
    "Container Recycling": "mdi:recycle",
    "Paper and Cardboard Recycling": "mdi:package-variant",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the Lane Cove Council website and search for your address. "
    "Use the exact address shown in the autocomplete result.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including suburb and postal code",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

API_URLS = {
    "search": "https://www.lanecove.nsw.gov.au/api/v1/myarea/search",
    "collection": "https://www.lanecove.nsw.gov.au/ocapi/Public/myarea/wasteservices",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.lanecove.nsw.gov.au/Services/Waste-and-Recycling/Waste-Collection-Calendar",
    "X-Requested-With": "XMLHttpRequest",
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        s.headers.update(HEADERS)

        r = s.get(API_URLS["search"], params={"keywords": self._address})
        r.raise_for_status()
        data = r.json()

        items = data.get("Items", [])
        if not items:
            raise SourceArgumentNotFound("address", self._address)

        if len(items) > 1:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [item["AddressSingleLine"] for item in items],
            )

        geoid = items[0]["Id"]

        r = s.get(
            API_URLS["collection"],
            params={"geolocationid": geoid, "ocsvclang": "en-AU"},
        )
        r.raise_for_status()

        html = r.json()["responseContent"]
        soup = BeautifulSoup(html, "html.parser")

        entries = []
        for article in soup.find_all("article"):
            waste_type = article.find("h3").get_text(strip=True)

            next_date_str = article.find("div", class_="next-service").get_text(
                strip=True
            )
            next_date = datetime.datetime.strptime(next_date_str, "%a %d/%m/%Y").date()

            icon = None
            for key, value in ICON_MAP.items():
                if key in waste_type:
                    icon = value
                    break

            entries.append(Collection(date=next_date, t=waste_type, icon=icon))

        return entries
