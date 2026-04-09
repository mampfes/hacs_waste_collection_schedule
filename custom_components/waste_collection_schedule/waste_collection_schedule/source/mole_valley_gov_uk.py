import re
from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,  # type: ignore[attr-defined]
)

# The server does not send its intermediate CA certificate, causing SSL
# verification to fail. suppress the resulting warnings.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "Mole Valley District Council"
DESCRIPTION = (
    "Source for molevalley.gov.uk services for Mole Valley District Council, UK."
)
URL = "https://www.molevalley.gov.uk"
TEST_CASES = {
    "44 Chapel Court Dorking": {
        "postcode": "RH4 1BT",
        "house_number": "44",
    },
    "79 Ashcombe Road Dorking": {
        "postcode": "RH4 1LX",
        "house_number": "79",
    },
    "21 Rookery Close Fetcham": {
        "postcode": "KT22 9BG",
        "house_number": "21",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your postcode and house number or name. You can verify your address at https://myproperty.molevalley.gov.uk/molevalley/",
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "house_number": "House Number or Name",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your property's postcode, e.g. KT22 9BG",
        "house_number": "Your house number or name, e.g. 17 or Rose Cottage",
    },
}

ICON_MAP = {
    "Refuse (black bin)": "mdi:trash-can",
    "Recycling (green bin)": "mdi:recycle",
    "Garden Waste (brown lid)": "mdi:leaf",
    "Food Waste": "mdi:food-apple",
}

API_URL = "https://myproperty.molevalley.gov.uk/molevalley/api/live_addresses/"

# Date format returned by the API: "(Wed) 08/04/2026"
DATE_FORMAT = "(%a) %d/%m/%Y"

BIN_TYPES = [
    "Refuse (black bin)",
    "Recycling (green bin)",
    "Garden Waste (brown lid)",
    "Food Waste",
]


class Source:
    def __init__(self, postcode: str, house_number: str):
        self._postcode = postcode.strip()
        self._house_number = house_number.strip().lower()

    def fetch(self) -> list[Collection]:
        page = 1
        suggestions = []

        while True:
            r = requests.get(
                API_URL + self._postcode,
                params={"page": page},
                timeout=30,
                verify=False,  # server does not send intermediate CA cert
            )
            r.raise_for_status()
            data = r.json()

            # API returns {"result": false} when page is out of range
            if not data.get("result", True):
                break

            features = data.get("results", {}).get("features", [])
            if not features:
                break

            for f in features:
                address = f["properties"]["address_string"]
                suggestions.append(address)
                # Match on full word/token boundary so "1" doesn't match "10", "11", etc.
                if re.match(
                    r"^" + re.escape(self._house_number) + r"[\s,]",
                    address.lower(),
                ):
                    return self._parse_collections(
                        f["properties"]["three_column_layout_html"]
                    )

            page += 1

        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", self._house_number, suggestions
        )

    def _parse_collections(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries = []

        for bin_type in BIN_TYPES:
            label_tag = soup.find("strong", string=re.compile(re.escape(bin_type)))
            if not label_tag:
                continue

            next_p = label_tag.find_next("p")
            if not next_p:
                continue

            date_tag = next_p.find("strong")
            if not date_tag:
                continue

            date_str = date_tag.get_text(strip=True)

            if "No collection" in date_str or "Not a" in date_str:
                continue

            try:
                collection_date = datetime.strptime(date_str, DATE_FORMAT).date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
