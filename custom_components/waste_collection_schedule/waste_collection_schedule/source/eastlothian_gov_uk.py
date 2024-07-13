import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Lothian"
DESCRIPTION = "Source for East Lothian."
URL = "https://www.eastlothian.gov.uk/"
TEST_CASES = {
    "EH21 8GU 4 Laing Loan, Wallyford": {
        "postcode": "EH218GU",
        "address": "4 Laing Loan",
    },
    "EH41 4LN Peterhouse, Morham, Haddington, EH41 4LN": {
        "postcode": "EH41 4LN",
        "address": "Peterhouse, Morham, Haddington",
    },
    "ELC-C26071": {"address_id": "ELC-C26071"},
}
_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "non recyclable waste": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
    "food waste": "mdi:food",
}


BASE_URL = "http://collectiondates.eastlothian.gov.uk"
START_URL = f"{BASE_URL}/your-calendar"
STREETS_URL_REGEX = re.compile(r'url\s*:\s*"(.*?)\?postcode=')
COLLECTION_URL_REGEX = re.compile(r'url\s*:\s*"(.*?)\?id="\s*\+\s*selectStreet')


class Source:
    def __init__(
        self,
        postcode: str | None = None,
        address: str | None = None,
        address_id: str | None = None,
    ):
        self._postcode: str | None = postcode.strip() if postcode else None
        self._address: str | None = (
            address.lower().replace(" ", "") if address else None
        )
        self._address_id: str | None = address_id.strip() if address_id else None
        self._collection_url: str | None = None
        self._streets_url: str | None = None

        if (not self._postcode or not self._address) and not self._address_id:
            raise ValueError("(postcode and address) or (address_id) required")
        # add space in postcode
        if postcode and " " not in postcode:
            self._postcode = postcode[:-3] + " " + postcode[-3:]

    def _address_match(self, other: str, level=0) -> bool:
        if not self._address:
            raise ValueError("Address required")
        other = other.lower().replace(" ", "")
        if level == 0:
            return self._address == other
        elif level == 1:
            return other.split(",")[:-1] != [] and other.split(",")[:-1] in (
                [self._address],
                self._address.split(",")[:-1],
            )
        elif level == 2:
            return other.split(",")[:-2] != [] and other.split(",")[:-2] in (
                [self._address],
                self._address.split(",")[:-1],
                self._address.split(",")[:-2],
            )
        return False

    def _retrieve_address_id(self) -> None:
        if self._streets_url is None:
            raise ValueError("API URL not set")
        if not self._postcode or not self._address:
            raise ValueError("Postcode and address required")

        params = {
            "postcode": self._postcode,
        }

        r = requests.get(self._streets_url, params=params)

        try:
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            select = soup.find("select", id="SelectStreet")
            if not isinstance(select, Tag):
                raise ValueError("No address options found")
            options = select.find_all("option")
        except Exception as e:
            raise ValueError("Invalid postcode Request recheck postcode") from e

        for level in range(3):
            for option in options:
                if self._address_match(option.text, level):
                    self._address_id = option["value"]
                    return
        raise ValueError(
            f"Address not found, use one of {', '.join([option.text for option in options])}"
        )

    def _get_colledctions(self) -> list[Collection]:
        if not self._collection_url:
            raise ValueError("API URL required")
        if not self._address_id:
            raise ValueError("Address ID required")
        params = {"id": self._address_id}
        r = requests.get(self._collection_url, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        calendar_item = soup.find_all("div", class_="calendar-item")
        entries: list[Collection] = []
        for item in calendar_item:
            types = item.find("div", class_="waste-label").text.split("&")
            date_string = item.find("div", class_="waste-value").text
            try:
                date_string = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_string)
                d = datetime.strptime(date_string, "%A %d %B %Y").date()
            except ValueError:
                _LOGGER.info(f"Failed to parse date: {date_string}, skipping")
                continue

            for type in types:
                type = type.replace(" is:", "").strip()
                icon = ICON_MAP.get(type.lower())
                entries.append(Collection(date=d, t=type, icon=icon))

        if len(entries) == 0:
            raise ValueError("No collections found")

        return entries

    def _retrieve_api_url(self) -> None:
        r = requests.get(START_URL)
        r.raise_for_status()
        collection_match = COLLECTION_URL_REGEX.search(r.text)
        streets_match = STREETS_URL_REGEX.search(r.text)
        if not collection_match or not streets_match:
            raise ValueError("API URL not found")
        self._streets_url = streets_match.group(1)
        self._collection_url = collection_match.group(1)
        if self._collection_url.startswith("/"):
            self._collection_url = BASE_URL + self._collection_url
        if self._streets_url.startswith("/"):
            self._streets_url = BASE_URL + self._streets_url

    def fetch(self) -> list[Collection]:
        fresh = 0
        if not self._collection_url:
            self._retrieve_api_url()
            fresh += 1
        if not self._address_id:
            self._retrieve_address_id()
            fresh += 1
        try:
            return self._get_colledctions()
        except Exception as e:
            if not self._postcode or not self._address:
                raise Exception(
                    "failed to get collections for address_id: recheck id or use postcode and address"
                ) from e
            if fresh == 2:
                raise e
            self._retrieve_api_url()
            self._retrieve_address_id()
            return self._get_colledctions()
