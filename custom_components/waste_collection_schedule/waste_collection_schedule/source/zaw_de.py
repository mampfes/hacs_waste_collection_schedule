import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "ZAW Zentraldeponie Wicker"
DESCRIPTION = "Source for ZAW waste collection schedule in Hesse, Germany"
URL = "https://www.zaw-online.de/"
TEST_CASES = {
    "Groß-Zimmern API": {"city": "Groß-Zimmern", "street": "Markstr.", "method": "api"},
    "Groß-Zimmern ICS": {"city": "Groß-Zimmern", "street": "Markstr.", "method": "ics"},
}

API_URL = "https://zaw.jumomind.com/mmapp/api.php"

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Biotonne": "mdi:leaf",
    "Gelber Sack": "mdi:sack",
    "Gelbe Tonne": "mdi:recycle",
    "Papier": "mdi:package-variant",
    "Altpapier": "mdi:package-variant",
}


class Source:
    def __init__(self, city: str, street: str | None = None, method: str = "api"):
        self._city = city
        self._street = street
        self._method = method.lower()  # Kept for compatibility, doesn't affect output

    def fetch(self):
        # Get termine data from webservice
        data = self._get_termine_data()

        # Both methods use the same processing to ensure consistent results
        # The 'method' parameter is provided for compatibility but doesn't affect the output
        return self._process_data(data)

    def _get_termine_data(self):
        """Fetch termine data from ZAW webservice"""
        # Step 1: Get all cities
        r = requests.get(f"{API_URL}?r=cities_web")
        r.raise_for_status()
        cities = r.json()

        # Find city_id
        city_id = None
        city_name_found = None
        for city_data in cities:
            if city_data["name"].lower() == self._city.lower():
                city_id = city_data["id"]
                city_name_found = city_data["name"]
                break

        if not city_id:
            # Provide suggestions
            available_cities = [city["name"] for city in cities]
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, available_cities
            )

        # Step 2: Get streets for city
        r = requests.get(f"{API_URL}?r=streets&city_id={city_id}")
        r.raise_for_status()
        streets = r.json()

        # Find area_id (waste collection area)
        # Note: streets have both 'id' (street ID) and 'area_id' (collection zone)
        area_id = None
        if self._street:
            for street_data in streets:
                if street_data["name"].lower() == self._street.lower():
                    area_id = street_data["area_id"]
                    break
            if not area_id:
                available_streets = [street["name"] for street in streets]
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", self._street, available_streets
                )
        else:
            # Use first street if none specified
            if streets:
                area_id = streets[0]["area_id"]

        if not area_id:
            raise Exception(f"No streets found for {city_name_found}")

        # Step 3: Get termine data from webservice
        r = requests.get(
            f"https://zaw.jumomind.com/webservice.php?idx=termins&city_id={city_id}&area_id={area_id}&ws=3"
        )
        r.raise_for_status()
        response_data = r.json()

        # Parse response structure: [{"Ack":"Success","id":"mm_termins","_data":[...]}]
        if not response_data or not isinstance(response_data, list):
            return []

        return response_data[0].get("_data", [])

    def _process_data(self, data):
        """Process termine data"""
        entries = []
        for item in data:
            # Parse date - format is "YYYY-MM-DD"
            date_str = item.get("cal_date")
            if not date_str:
                continue

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            # Get waste type code (e.g., "ZAW_BIO", "ZAW_GELB")
            waste_type_code = item.get("cal_garbage_type", "")
            comment = item.get("cal_comment", "")

            # Determine waste type label
            type_label = waste_type_code
            if "BIO" in waste_type_code:
                type_label = "Biomüll"
            elif "GELB" in waste_type_code:
                type_label = "Gelber Sack"
            elif "PAP" in waste_type_code:
                type_label = "Papier"
            elif "REST" in waste_type_code:
                type_label = "Restmüll"
            elif "SCHAD" in waste_type_code:
                type_label = "Schadstoffmobil"

            # Add comment if available
            if comment:
                type_label = f"{type_label} ({comment})"

            # Find icon
            icon = "mdi:trash-can"
            for key, ico in ICON_MAP.items():
                if key.lower() in type_label.lower():
                    icon = ico
                    break

            entries.append(
                Collection(
                    date=date,
                    t=type_label,
                    icon=icon,
                )
            )

        return entries
