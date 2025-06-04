import datetime
import logging
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "Shoalhaven City Council"
DESCRIPTION = "Source script for shoalhaven.nsw.gov.au"
URL = "https://www.shoalhaven.nsw.gov.au/"
TEST_CASES = {
    # Example Geolocation ID from the provided URL.
    "Elizabeth Dr, VINCENTIA": {
        "geolocation_id": "2ea7b0c7-b627-421d-8436-248b8da384b6"
    },
    "The Park Dr, SANCTUARY POINT": {
        "geolocation_id": "b0b35bab-76c1-4b58-b609-115da3fa3829"
    },
    "Station St, NOWRA": {"geolocation_id": "984061de-cd63-43f4-bbd3-694b4e8af4d5"},
}

API_BASE_URL = "https://www.shoalhaven.nsw.gov.au/ocapi/Public/myarea/wasteservices"
ICON_MAP = {
    # Maps waste types (in uppercase) to Material Design Icons (mdi)
    "GENERAL WASTE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": """
    To get your Geolocation ID:
    1. Go to the Shoalhaven City Council 'My Area' page: <https://www.shoalhaven.nsw.gov.au/My-Area>
    2. Open Developer Tools in your browser by pressing F12 and go to the Network tab.
    3. Enter your address in the search bar and select it from the suggestions.
    4. Once your address information is displayed, look at the 'wasteservices' URL in the Network tab.
    5. Copy the long string of letters and numbers that follows 'geolocationid=' (e.g., 2ea7b0c7-b627-421d-8436-248b8da384b6). This is your Geolocation ID.
    """,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "geolocation_id": "Your unique Geolocation ID for the address (e.g., 2ea7b0c7-b627-421d-8436-248b8da384b6)",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "geolocation_id": "Geolocation ID",
    },
}

# ### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, geolocation_id: str):
        """
        Initialize the Source with the provided geolocation ID.

        :param geolocation_id: The unique ID for the address to fetch waste services for.
        """
        self._geolocation_id = geolocation_id

    def fetch(self) -> list[Collection]:
        """
        Fetch the waste collection schedule from the Shoalhaven City Council API.

        :return: A list of Collection objects, each representing a waste collection.
        :raises Exception: If the API call fails or no collection schedules are found.
        """
        session = requests.Session()
        params = {"geolocationid": self._geolocation_id, "ocsvclang": "en-AU"}

        # Make the API request
        r = session.get(API_BASE_URL, params=params)
        r.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)

        data = r.json()

        # Check if the API call was successful based on the JSON response
        if not data.get("success"):
            raise Exception(
                f"API call was not successful: {data.get('responseContent', 'No specific error message provided by API.')}"
            )

        # The actual content is embedded as an HTML string within 'responseContent'
        html_content = data["responseContent"]
        soup = BeautifulSoup(html_content, "html.parser")

        entries = []  # List to store parsed collection schedules

        # Find all HTML blocks that represent a waste service result with a precise date.
        # This regex targets divs with both "waste-services-result" and "date-precise" classes.
        waste_service_blocks = soup.find_all(
            "div", class_=re.compile(r"\bwaste-services-result\b.*\bdate-precise\b")
        )

        for block in waste_service_blocks:
            waste_type_tag = block.find("h3")
            next_service_tag = block.find("div", class_="next-service")

            # These tags should always be present for blocks with 'date-precise'
            if waste_type_tag and next_service_tag:
                waste_type = waste_type_tag.get_text(strip=True).upper()
                next_service_text = next_service_tag.get_text(strip=True)

                # Extract the date using a regular expression.
                # The 'date-precise' class implies a date will be present.
                match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", next_service_text)
                if match:
                    date_str = match.group(1)
                    collection_date = datetime.datetime.strptime(
                        date_str, "%d/%m/%Y"
                    ).date()

                    entries.append(
                        Collection(
                            date=collection_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
                else:
                    # This case should ideally not be hit if 'date-precise' filtering works as expected.
                    _LOGGER.warning(
                        f"Warning: 'date-precise' block '{waste_type}' did not contain a parseable date: '{next_service_text}'"
                    )
            else:
                # This case should also not be hit with the refined find_all.
                _LOGGER.warning(
                    f"Warning: 'date-precise' block missing h3 or next-service div: {block}"
                )

        if not entries:
            # If no collection schedules were successfully parsed, raise an error.
            raise Exception(
                "No collection schedules found. Please check your Geolocation ID and ensure the API is returning valid data for your address."
            )

        return entries
