import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Kempsey Shire Council"
DESCRIPTION = "Source script for kempsey.nsw.gov.au waste collection services."
URL = "https://www.kempsey.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "10-12 Smith Street Kempsey": {"address": "10-12 Smith Street Kempsey"},
    "1 Belgrave Street Kempsey": {"address": "1 Belgrave Street Kempsey"},
}

API_SEARCH_URL = "https://www.kempsey.nsw.gov.au/api/v1/myarea/search"
API_WASTE_URL = "https://www.kempsey.nsw.gov.au/ocapi/Public/myarea/wasteservices"
API_WASTE_PAGE_LINK = "/$b9015858-988c-48a4-9473-7c193df083e4$/Residents/Waste-recycling/Waste-bin-collection"

# How many weeks ahead to generate the schedule
SCHEDULE_WEEKS = 26

ICON_MAP = {
    "Green Organics Bin": "mdi:leaf",
    "Red Rubbish Bin": "mdi:trash-can",
    "Yellow Recycling Bin": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your full street address as it appears on the Kempsey Shire Council website, e.g. '10-12 Smith Street Kempsey'.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your full street address including suburb, e.g. '10-12 Smith Street Kempsey'",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Full Street Address",
    },
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        # Step 1: Search for the address to get the geolocationid
        search_response = requests.get(
            API_SEARCH_URL,
            params={"keywords": self._address},
            timeout=30,
        )
        search_response.raise_for_status()
        search_data = search_response.json()

        items = search_data.get("Items", [])
        if not items:
            raise SourceArgumentNotFound("address", self._address)

        geolocation_id = items[0].get("Id")
        if not geolocation_id:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Fetch waste services using the geolocationid
        waste_response = requests.get(
            API_WASTE_URL,
            params={
                "geolocationid": geolocation_id,
                "ocsvclang": "en-AU",
                "pageLink": API_WASTE_PAGE_LINK,
            },
            timeout=30,
        )
        waste_response.raise_for_status()

        # Step 3: Response is JSON — extract the HTML from responseContent
        waste_data = waste_response.json()
        html_content = waste_data.get("responseContent", "")
        if not html_content:
            raise Exception(
                f"Empty response from waste services API for address '{self._address}'."
            )

        soup = BeautifulSoup(html_content, "html.parser")
        results = soup.select(".waste-services-result")

        if not results:
            raise Exception(
                f"No waste services data found for address '{self._address}'. "
                "The address may not be serviced or the page structure may have changed."
            )

        # Step 4: Extract anchor dates for General Waste and Recycling
        general_waste_date = None
        recycling_date = None

        for result in results:
            heading = result.find("h3")
            if not heading:
                continue
            waste_type = heading.get_text(strip=True)

            next_service_div = result.select_one(".next-service")
            if not next_service_div:
                continue

            date_text = next_service_div.get_text(separator=" ", strip=True)
            date_matches = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", date_text)

            if date_matches:
                first_date = datetime.datetime.strptime(
                    date_matches[0], "%d/%m/%Y"
                ).date()
                if waste_type == "General Waste":
                    general_waste_date = first_date
                elif waste_type == "Recycling":
                    recycling_date = first_date

        if not general_waste_date and not recycling_date:
            raise Exception(
                f"Could not parse any collection dates for address '{self._address}'."
            )

        # Step 5: Build 26-week schedule.
        # Green Waste every week.
        # Week A (anchor) = General Waste + Green Waste
        # Week B = Recycling + Green Waste
        anchor_date = general_waste_date or recycling_date
        if anchor_date is None:
            return []
        entries = []

        for week in range(SCHEDULE_WEEKS):
            collection_date = anchor_date + datetime.timedelta(weeks=week)

            entries.append(
                Collection(
                    date=collection_date,
                    t="Green Organics Bin",
                    icon=ICON_MAP["Green Organics Bin"],
                )
            )

            if week % 2 == 0:
                entries.append(
                    Collection(
                        date=collection_date,
                        t="Red Rubbish Bin",
                        icon=ICON_MAP["Red Rubbish Bin"],
                    )
                )
            else:
                entries.append(
                    Collection(
                        date=collection_date,
                        t="Yellow Recycling Bin",
                        icon=ICON_MAP["Yellow Recycling Bin"],
                    )
                )

        return entries
