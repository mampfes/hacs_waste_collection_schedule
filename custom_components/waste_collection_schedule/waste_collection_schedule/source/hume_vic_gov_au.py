import datetime
from waste_collection_schedule import Collection

import re
import requests
import json
from datetime import datetime

TITLE = "Hume City Council"
DESCRIPTION = "Source for hume.vic.gov.au Waste Collection Services"
URL = "https://hume.vic.gov.au"
TEST_CASES = {
    "280 Somerton": {"address": "280 SOMERTON ROAD ROXBURGH PARK, VIC  3064"}, #Tuesday
    "1/90 Vineyard": {"address": "1/90 Vineyard Road Sunbury, VIC 3429"}, # Wednesday
    "33 Toyon": {"address": "33 TOYON ROAD KALKALLO  VIC  3064"}, #Friday
}


class Source:
    def __init__(self, address):
        address = address.strip()
        address = re.sub(' +', ' ', address)
        address = re.sub(',', '', address)
        address = re.sub('victoria (\d{4})', 'VIC \\1', address, flags=re.IGNORECASE)
        address = re.sub(' vic (\d{4})', '  VIC  \\1', address, flags=re.IGNORECASE)
        self._address = address

    def fetch(self):
        entries = []

        #initiate a session
        url = "https://maps.hume.vic.gov.au/IntraMaps98/ApplicationEngine/Projects/"

        payload={}
        params = {
            "configId": "00000000-0000-0000-0000-000000000000",
            "appType": "MapBuilder",
            "project": "040e29e4-597b-4e47-9f49-6f37d3e694cb",
            "datasetCode": ""
        }
        headers = {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        sessionid = response.headers['X-IntraMaps-Session']



        #Load the Map Project (further requests don't appear to work if this request is not made)
        url = "https://maps.hume.vic.gov.au/IntraMaps98/ApplicationEngine/Modules/"

        payload = json.dumps({
          "module": "bf9446ea-5eb5-4f76-b776-dcee7f4b488b",
          "includeWktInSelection": True,
          "includeBasemaps": False
        })

        params = {
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)



        #search for the address
        url = "https://maps.hume.vic.gov.au/IntraMaps98/ApplicationEngine/Search/"

        payload = json.dumps({
          "fields": [
            self._address
          ]
        })

        params = {
            "infoPanelWidth": "0",
            "mode": "Refresh",
            "form": "671222d7-d004-4cc1-b4a8-4babef3412fa",
            "resubmit": "false",
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        
        fields_json = response.json()['infoPanels']['info1']['feature']['fields']

        date_rubbish = fields_json[9]['value']['value'].split(" ")[1]
        date_recycling = fields_json[9]['value']['value'].split(" ")[1]
        date_green_waste = fields_json[9]['value']['value'].split(" ")[1]



        #general rubbish (red lid)
        entries.append(
            Collection(
                date = datetime.strptime(date_rubbish,"%d/%m/%Y").date(),
                t = "Rubbish",
                icon = "mdi:rubbish-bin", 
            )
        )
        
        #general recycling (yellow lid)
        entries.append(
            Collection(
                date = datetime.strptime(date_recycling,"%d/%m/%Y").date(),
                t = "Recycling",
                icon = "mdi:recycle", 
            )
        )

        #green waste (green lid)
        entries.append(
            Collection(
                date = datetime.strptime(date_green_waste,"%d/%m/%Y").date(),
                t = "Green Waste",
                icon = "mdi:leaf", 
            )
        )

        return entries
