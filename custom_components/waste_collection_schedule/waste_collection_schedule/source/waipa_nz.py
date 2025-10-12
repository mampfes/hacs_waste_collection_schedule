import json
from datetime import datetime

import requests

from waste_collection_schedule import Collection

TITLE = "Waipa District Council"
DESCRIPTION = "Source for Waipa District Council. Finds both general and glass recycling dates."
URL = "https://www.waipadc.govt.nz/"
TEST_CASES = {
    "10 Queen Street": {"address": "10 Queen Street"}, # Monday
    "1 Acacia Avenue": {"address": "1 Acacia Avenue"}, # Wednesday
}

ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
}


class Source:
    def __init__(self, address):
        self._address = address

    def _parse_collection_dates(self, dates_text, collection_type):
        """
        Parse collection dates from the API response text.
        
        Expected format: "Will be collected on DD-MMM-YYYY, and then will be collected in two weeks on DD-MMM-YYYY"
        
        Args:
            dates_text: The text containing collection dates
            collection_type: The type of collection (e.g., "Recycling", "Glass")
            
        Returns:
            List of Collection objects
        """
        parts = dates_text.split(" on ")
        if len(parts) < 3:
            raise Exception(f"Unexpected {collection_type} date format: {dates_text}")
        
        first_date = parts[1].split(",")[0]  # Extract "DD-MMM-YYYY"
        second_date = parts[2]  # Extract "DD-MMM-YYYY"
        
        icon = ICON_MAP.get(collection_type)
        
        return [
            Collection(
                datetime.strptime(first_date, "%d-%b-%Y").date(),
                collection_type,
                icon=icon
            ),
            Collection(
                datetime.strptime(second_date, "%d-%b-%Y").date(),
                collection_type,
                icon=icon
            )
        ]

    def fetch(self):
        entries = []

        # Initiate a session
        url = "https://waipadc.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Projects/"

        payload = {}
        params = {
            "configId": "6aa41407-1db8-44e1-8487-0b9a08965283",
            "appType": "MapBuilder",
            "project": "b5bc138e-edce-4b01-b159-ec44539ab455",
            "datasetCode": ""
        }
        headers = {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        
        if 'X-IntraMaps-Session' not in response.headers:
            raise Exception("Failed to initiate session: X-IntraMaps-Session header not found")
        
        sessionid = response.headers['X-IntraMaps-Session']

        # Load the Map Project (further requests don't appear to work if this request is not made)
        url = "https://waipadc.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Modules/"

        payload = json.dumps({
          "module": "5373c4e1-c975-4c8f-b51a-0ac976f5313c",
          "includeWktInSelection": True,
          "includeBasemaps": False
        })

        params = {
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)

        # Search for the address
        url = "https://waipadc.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Search/"

        payload = json.dumps({
          "fields": [
            self._address
          ]
        })

        params = {
            "infoPanelWidth": "0",
            "mode": "Refresh",
            "form": "e6677a33-9d47-407a-b199-5c7967a4be07",
            "resubmit": "false",
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        
        # This request may return multiple addresses. Use the first one.
        search_results = response.json()
        
        if not search_results.get('fullText') or len(search_results['fullText']) == 0:
            raise Exception(f"No addresses found for '{self._address}'")
        
        address_map_key = search_results['fullText'][0]['mapKey']

        # Lookup the specific property data
        url = "https://waipadc.spatial.t1cloud.com/spatial/IntraMaps/ApplicationEngine/Search/Refine/Set"

        payload = json.dumps({
          "selectionLayer": "e7163a17-2f10-42b1-8dbf-8c53adf089a8",
          "mapKey": address_map_key,
          "infoPanelWidth": 350,
          "mode": "Refresh",
          "dbKey": address_map_key,
          "zoomType": "current"
        })

        params = {
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        property_data = response.json()

        # Validate the response structure
        try:
            fields = property_data['infoPanels']['info1']['feature']['fields']
        except (KeyError, TypeError) as e:
            raise Exception(f"Unexpected API response structure: {e}")
        
        if len(fields) < 4:
            raise Exception(f"Expected at least 4 fields in API response, got {len(fields)}")

        # General recycling (yellow bin) - field [2]
        general_recycling_dates_text = fields[2]['value']['value']
        entries.extend(self._parse_collection_dates(general_recycling_dates_text, "Recycling"))

        # Glass recycling (blue bin) - field [3]
        glass_recycling_dates_text = fields[3]['value']['value']
        entries.extend(self._parse_collection_dates(glass_recycling_dates_text, "Glass"))

        return entries
