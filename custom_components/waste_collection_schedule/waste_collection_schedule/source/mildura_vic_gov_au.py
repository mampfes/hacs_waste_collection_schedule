import json
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Mildura Rural City Council"
DESCRIPTION = "Source for Mildura Rural City Council waste collection."
URL = "https://www.mildura.vic.gov.au"
TEST_CASES = {
    "Stockmans Drive": {"street_address": "1 Stockmans Drive, Irymple VIC 3498"},
    "Deakin Avenue": {"street_address": "76 Deakin Avenue, Mildura VIC 3500"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Full street address including suburb and postcode, e.g. '1 Stockmans Drive, Irymple VIC 3498'",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to <https://www.mildura.vic.gov.au/Explore/My-Neighbourhood> and make sure your address matches the auto-complete suggestions."
}

API_URLS = {
    "address_search": "https://www.mildura.vic.gov.au/api/v1/myarea/search",
    "collection": "https://www.mildura.vic.gov.au/ocapi/Public/myarea/wasteservices",
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept": "text/plain, */*; q=0.01",
    "Referer": "https://www.mildura.vic.gov.au/Services/Waste-and-Recycling/My-bins/Find-your-bin-day",
    "X-Requested-With": "XMLHttpRequest",
}

ICON_MAP = {
    "Organics Waste": Icons.BIO_KITCHEN,
    "Landfill Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Glass": Icons.GLASS,
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        # Step 1: search for the address to get its geolocation id
        r = session.get(
            API_URLS["address_search"],
            params={"keywords": self._street_address},
            headers=HEADERS,
        )
        r.raise_for_status()

        data = json.loads(r.text)

        items = data.get("Items") or []
        if not items:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Check your address at https://www.mildura.vic.gov.au/Explore/My-Neighbourhood",
            )

        location_id = items[0]["Id"]

        # Step 2: retrieve the upcoming collections for the property
        r = session.get(
            API_URLS["collection"],
            params={"geolocationid": location_id, "ocsvclang": "en-AU"},
            headers=HEADERS,
        )
        r.raise_for_status()

        data = json.loads(r.text)

        response_content = data["responseContent"]

        soup = BeautifulSoup(response_content, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            date_text = item.find("div", attrs={"class": "next-service"})
            if date_text is None:
                continue

            date_format = "%a %d/%m/%Y"

            try:
                cleaned_date_text = (
                    date_text.text.replace("\r", "").replace("\n", "").strip()
                )
                date = datetime.strptime(cleaned_date_text, date_format).date()
            except ValueError:
                # Non-date entries, e.g. "Bin Collection Area: You are in Area 1"
                continue

            waste_type_h3 = item.find("h3")
            if waste_type_h3 is None:
                continue
            waste_type = waste_type_h3.text.strip()

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, Icons.GENERAL_WASTE),
                )
            )

        return entries
