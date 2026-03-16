import datetime
import json
import logging
import urllib.parse
import zoneinfo
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException, SourceArgumentNotFound

_LOGGER = logging.getLogger(__name__)

TITLE = "RessourceIndsamling.dk"  # Title will show up in README.md and info.md
DESCRIPTION = "Source for RessourceIndsamling.dk collection"  # Describe your source
URL = "https://www.ressourceindsamling.dk/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Home": {"streetName": "Kløvertoften", "number": "61"}
}

API_URL = "https://selfserviceapi.waste2x.dk/api/Services/Services/GetServicesForCustomer"
ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "Haveaffald": "mdi:leaf",
    "Storskrald": "mdi:recycle",
    "Mad/Rest affald": "mdi:food",
    "Pap": "mdi:archive",
    "Papir/Plast \u0026 MDK": "mdi:bottle-soda",
    "Metal/Glas affald": "mdi:wrench",
    "Juletræer": "mdi:pine-tree",
    "Farligt affald": "mdi:biohazard",
}

ADDRESS_LOOKUP_URL = "https://selfserviceapi.waste2x.dk/api/Customer/Customer/SearchCustomer/"


class Source:
    def __init__(self, streetName, number):
        self._streetName = streetName
        self._number = number

    def fetch(self):
        entries = []  # List that holds collection schedule

        term = self._streetName + " " + self._number

        _LOGGER.info("Fetching addressId from waste2x.dk: " + term)

        headers = {"organizationid": "76fbcd50-996e-4b0e-8b5b-3e9e49cea6d6"}
        query = urllib.parse.quote(term.lower() + "%") # trailing % is important
        url_encoded = ADDRESS_LOOKUP_URL + query 
        _LOGGER.info(f"Request URL: {url_encoded}")
        address_response = requests.get(url_encoded, headers=headers, timeout=30)
        _LOGGER.debug(f"Address lookup response status: {address_response.status_code}")
        _LOGGER.debug(f"Address lookup response: {address_response.text}")
        if address_response.status_code != 200:
            raise SourceArgumentNotFound("streetName", term, f"Failed to lookup address: HTTP {address_response.status_code}")

        try:
            response_data = address_response.json()
        except json.JSONDecodeError as e:
            _LOGGER.error("Failed to parse address lookup JSON response: %s", e)
            raise ValueError(f"Failed to parse address lookup response: {e}")
        
        _LOGGER.debug(f"Address search response: {response_data}")

        if "items" not in response_data or not response_data["items"]:
            raise SourceArgumentException(
                "streetName",
                f"Address '{term}' not found in waste2x.dk database.",
            )
        
        customer_Id = response_data["items"][0]["customerId"]

        _LOGGER.info("Fetching data from waste2x.dk")
        # Use Copenhagen timezone to handle DST correctly
        
        tz = zoneinfo.ZoneInfo("Europe/Copenhagen")
        now = datetime.datetime.now(tz)
        start_date = now.strftime("%Y-%m-%dT%H:%M:%S.000%z")
        end_date = (now + datetime.timedelta(days=31)).strftime("%Y-%m-%dT%H:%M:%S.000%z")
        
        # Format timezone with colon (e.g., +01:00 instead of +0100)
        start_date = start_date[:-2] + ":" + start_date[-2:]
        end_date = end_date[:-2] + ":" + end_date[-2:]

        url = f"{API_URL}/{customer_Id}/{start_date}/{end_date}"
        response = requests.get(url, headers=headers, timeout=30)
        _LOGGER.debug(f"Services response status: {response.status_code}")
        _LOGGER.debug(f"Services response: {response.text}")
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch services: HTTP {response.status_code}")
        
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            _LOGGER.error("Failed to parse services JSON response: %s", exc)
            raise ValueError("Failed to parse services response from waste2x.dk") from exc

        # Parse collection schedule data and create Collection objects
        for item in data:
            entries.append(
                Collection(
                    date=datetime.datetime.fromisoformat(item["startTime"]).date(),
                    t=item["serviceTypePublicName"],
                    icon=ICON_MAP.get(item["serviceTypePublicName"], "mdi:trash-can-outline"),
                )
            )

        return entries
