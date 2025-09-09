from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Cincinnati, OH"
DESCRIPTION = "City of Cincinnati, OH, USA"
URL = "https://www.cincinnati.gov/"
COUNTRY = "us"
TEST_CASES = {}
HEADERS = {"user-agent": "Mozilla/5.0"}
ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Street Sweeping": "mdi:road-variant",
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Find your address ID by searching for your address on Cincinnati's service website. The address ID is needed to retrieve collection schedules.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "addressid": "Address ID from Cincinnati's system (e.g., 00010GRAND0703640000)",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "addressid": "Address ID (e.g., 00010GRAND0703640000)",
    },
}


class Source:
    def __init__(self, addressid: str):
        self._addressid: str = addressid

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # Get JSON data from Cincinnati API
        url = f"https://cagismaps.hamilton-co.org/CSROnlineServices/api/CinciServices/GetServices?addressid={self._addressid}"
        response = s.get(url, headers=HEADERS)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        entries = []

        # Check if the response has the expected structure
        if "Services" not in data:
            return entries

        # Process each service
        for service in data["Services"]:
            service_type = service.get("ServiceType", "").title()

            # Skip street sweeping for now as it's not a regular waste collection
            if "Street Sweeping" in service_type:
                continue

            # Process service dates
            service_dates = service.get("ServiceDates", [])

            for service_date in service_dates:
                start_date_str = service_date.get("startDate")
                if not start_date_str:
                    continue

                # Parse the date string (format: "Wednesday, September 17, 2025")
                try:
                    date_obj = datetime.strptime(start_date_str, "%A, %B %d, %Y").date()
                    # Subtract one day from the collection date
                    date_obj = date_obj - timedelta(days=1)

                    # Map service types to collection names and icons
                    collection_type = service_date.get("serviceType", service_type)
                    icon = ICON_MAP.get(collection_type, "mdi:trash-can")

                    entries.append(
                        Collection(date=date_obj, t=collection_type, icon=icon)
                    )
                except ValueError:
                    # Skip if date parsing fails
                    continue

        return entries
