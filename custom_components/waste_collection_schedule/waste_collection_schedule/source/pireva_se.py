import re
from datetime import date, datetime
from typing import List

import bs4
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Pireva"
DESCRIPTION = "Source for Pireva that serves Piteå kommun, Sweden."
URL = "https://www.pireva.se/tomningsschema/"
TEST_CASES = {
    "Räddningstjänsten Mf": {"street_address": "Kolugnsvägen 1 Räddningstjänsten Mf"},
    "Piteå Sjukhus": {"street_address": "Oskar Forssells Väg 1 B Piteå Sjukhus"},
}
COUNTRY = "se"

SEARCH_URL = "https://www.pireva.se/api/search/collection-address"
DATA_URL_FORMAT = "https://www.pireva.se/tomningsschema/{SLUG}/"
ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple",
}
MONTH_MAP = {
    "Januari": 1,
    "Februari": 2,
    "Mars": 3,
    "April": 4,
    "Maj": 5,
    "Juni": 6,
    "Juli": 7,
    "Augusti": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "December": 12,
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> List[Collection]:
        slug = self.find_slug()
        if not slug:
            raise SourceArgumentException(
                "street_address",
                f"No returned building address for: {self._street_address}",
            )

        pickup_tables = self.find_pickup_months(slug)

        return self.parse_entries(pickup_tables)

    def find_slug(self) -> str:
        """Query Pireva search API for street address slug.

        Returns:
            str: Slug for address
        """
        response = requests.get(SEARCH_URL, params={"q": self._street_address})
        matched_addresses = response.json().get("matches")

        return next(
            (
                item["address_slug"]
                for item in matched_addresses
                if item.get("address") == self._street_address
            ),
            "",
        )

    @staticmethod
    def find_pickup_months(slug: str) -> bs4.ResultSet[bs4.Tag]:
        """Query Pireva data URL and find all HTML tables with pickup dates."""
        response_data_url = requests.get(DATA_URL_FORMAT.format(SLUG=slug))
        soup = bs4.BeautifulSoup(response_data_url.text, "html.parser")

        return soup.find_all("table")

    @staticmethod
    def parse_entries(pickup_tables: bs4.ResultSet[bs4.Tag]) -> List[Collection]:
        """Traverse and parse HTML data.

        Args:
            pickup_tables (bs4.ResultSet[Tag]): response from the website

        Returns:
            List[Collection]: list of Collection found
        """
        entries = []
        for table in pickup_tables:
            heading = table.select_one("thead th").text.strip()
            if heading in MONTH_MAP:
                year = datetime.now().year
                month = MONTH_MAP.get(heading)
            else:
                month_string, year = heading.split(" ")
                month = MONTH_MAP.get(month_string)

            if not month:
                continue

            pickups = table.select("tbody tr")
            for pickup in pickups:
                cells = pickup.select("td")
                waste_type = cells[0].text
                day = re.sub(r"\D", "", cells[1].text)
                next_pickup_date = date(int(year), month, int(day))

                entries.append(
                    Collection(
                        date=next_pickup_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
