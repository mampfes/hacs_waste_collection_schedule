import requests
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Republic Services"
DESCRIPTION = "Source for Republic Services waste collection."
URL = "https://www.republicservices.com"
TEST_CASES = {
    "ParmaHeights": {"street": "Mandalay Dr", "zip": "44130"},
}

API_URL = "https://www.republicservices.com/api/v1/public/schedule"

class Source:
    def __init__(self, street, zip):
        self.street = street
        self.zip = zip

    def fetch(self):
        params = {
            "streetAddress": self.street,
            "zipCode": self.zip,
        }

        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()

        entries = []

        # Republic Services returns multiple service types
        for service in data.get("services", []):
            service_type = service.get("serviceType")
            for event in service.get("events", []):
                date_str = event.get("serviceDate")
                if not date_str:
                    continue

                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                entries.append(Collection(date=date, t=service_type))

        return entries
