import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Central Bedfordshire Council"
DESCRIPTION = (
    "Source for www.centralbedfordshire.gov.uk services for Central Bedfordshire"
)
URL = "https://www.centralbedfordshire.gov.uk"
TEST_CASES = {
    "postcode has space": {"postcode": "SG15 6YF", "house_name": "10 Old School Walk"},
    "postcode without space": {
        "postcode": "SG180LL",
        "house_name": "1 Chestnut Avenue",
    },
}

ICON_MAP = {
    "Refuse (black bin)": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden waste": "mdi:leaf",
    "Food waste": "mdi:food-apple",
}


class Source:
    def __init__(self, postcode, house_name):
        self._postcode = postcode
        self._house_name = house_name

    def fetch(self):
        session = requests.Session()

        # Add realistic browser headers to avoid bot detection
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Cache-Control": "max-age=0",
            }
        )

        # First, visit the page to establish session
        url = "https://www.centralbedfordshire.gov.uk/info/163/bins_and_waste_collections_-_check_bin_collection_days"

        try:
            # Initial page load to get session cookies
            session.get(url, timeout=30)
            time.sleep(2)  # Be polite to the server

            # Lookup postcode, then use house name to get UPRN
            data = {
                "postcode": self._postcode,
            }

            r = session.post(url, data=data, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, features="html.parser")

            # Check if we got blocked or redirected
            if "403" in r.text or "forbidden" in r.text.lower():
                raise requests.exceptions.HTTPError(
                    "403 Forbidden - IP may be temporarily blocked"
                )

            address_select = soup.find("select", id="address")
            if not address_select:
                raise ValueError(
                    "Could not find address selection dropdown - page structure may have changed"
                )

            address = address_select.find(
                "option",
                text=lambda value: value and value.startswith(self._house_name),
            )

            if address is None:
                addresses = {
                    option.text.removeprefix(self._postcode)
                    for option in address_select.select("option")
                } - {""}
                raise SourceArgumentNotFoundWithSuggestions(
                    "house_name",
                    self._house_name,
                    addresses,
                )

            self._uprn = address["value"]

            # Add some delay between requests
            time.sleep(3)

            data = {
                "address_text": address.text,
                "address": self._uprn,
                "postcode": self._postcode,
            }

            r = session.post(url, data=data, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, features="html.parser")
            collections_div = soup.find("div", id="collections")

            if not collections_div:
                raise ValueError(
                    "Could not find collections data - page structure may have changed"
                )

            s = collections_div.find_all("h3")
            entries = []

            for collection in s:
                try:
                    date = datetime.strptime(collection.text, "%A, %d %B %Y").date()
                    for sibling in collection.next_siblings:
                        if (
                            sibling.name == "h3"
                            or sibling.name == "p"
                            or sibling.name == "a"
                            or sibling.name == "div"
                        ):
                            break
                        if (
                            sibling.name != "br"
                            and hasattr(sibling, "text")
                            and sibling.text.strip()
                        ):
                            entries.append(
                                Collection(
                                    date=date,
                                    t=sibling.text.strip(),
                                    icon=ICON_MAP.get(sibling.text.strip()),
                                )
                            )
                except ValueError:
                    # Skip dates that can't be parsed
                    continue

            return entries

        except requests.exceptions.RequestException as e:
            if "403" in str(e):
                raise requests.exceptions.HTTPError(
                    f"403 Forbidden - Central Bedfordshire Council is blocking requests. "
                    f"Try again later or check if your IP is temporarily banned. Error: {e}"
                ) from e
            else:
                raise e
