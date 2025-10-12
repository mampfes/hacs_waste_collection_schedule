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


class Source:
    def __init__(self, address):
        self._address = address

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

        # General recycling (yellow bin) - field [2]
        general_recycling_dates_text = property_data['infoPanels']['info1']['feature']['fields'][2]['value']['value']
        # New format: "Will be collected on 13-Oct-2025, and then will be collected in two weeks on 27-Oct-2025"
        # Extract dates: split by "on " and take the dates
        recycling_parts = general_recycling_dates_text.split(" on ")
        if len(recycling_parts) < 3:
            raise Exception(f"Unexpected recycling date format: {general_recycling_dates_text}")
        
        first_date = recycling_parts[1].split(",")[0]  # "13-Oct-2025"
        second_date = recycling_parts[2]  # "27-Oct-2025"
        
        entries.append(
            Collection(
                datetime.strptime(first_date, "%d-%b-%Y").date(),
                "Recycling"
            )
        )
        entries.append(
            Collection(
                datetime.strptime(second_date, "%d-%b-%Y").date(),
                "Recycling"
            )
        )

        # Glass recycling (blue bin) - field [3]
        glass_recycling_dates_text = property_data['infoPanels']['info1']['feature']['fields'][3]['value']['value']
        # Same format as above
        glass_parts = glass_recycling_dates_text.split(" on ")
        if len(glass_parts) < 3:
            raise Exception(f"Unexpected glass date format: {glass_recycling_dates_text}")
        
        first_date = glass_parts[1].split(",")[0]  # "20-Oct-2025"
        second_date = glass_parts[2]  # "17-Nov-2025"
        
        entries.append(
            Collection(
                datetime.strptime(first_date, "%d-%b-%Y").date(),
                "Glass"
            )
        )
        entries.append(
            Collection(
                datetime.strptime(second_date, "%d-%b-%Y").date(),
                "Glass"
            )
        )

        return entries
