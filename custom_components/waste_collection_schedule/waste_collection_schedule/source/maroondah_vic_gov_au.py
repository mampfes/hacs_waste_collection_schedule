import datetime
from waste_collection_schedule import Collection

import requests
import json
from datetime import datetime

TITLE = "Maroondah City Council"
DESCRIPTION = "Source for Maroondah City Council. Finds both green waste and general recycling dates."
URL = "https://www.maroondah.vic.gov.au/"
TEST_CASES = {
    "Monday - Area A": {"address": "1 Abbey Court, RINGWOOD 3134"}, # Monday - Area A
    "Monday - Area B": {"address": "1 Angelica Crescent, CROYDON HILLS 3136"}, # Monday - Area B
    "Tuesday - Area B": {"address": "6 Como Close, CROYDON 3136"}, # Tuesday - Area B
    "Wednesday - Area A": {"address": "113 Dublin Road, RINGWOOD EAST 3135"}, # Wednesday - Area A
    "Wednesday - Area B": {"address": "282 Maroondah Highway, RINGWOOD 3134"}, # Wednesday - Area B
    "Thursday - Area A": {"address": "4 Albury Court, CROYDON NORTH 3136"}, # Thursday - Area A
    "Thursday - Area B": {"address": "54 Lincoln Road, CROYDON 3136"}, # Thursday - Area B
    "Friday - Area A": {"address": "6 Lionel Crescent, CROYDON 3136"}, # Friday - Area A
    "Friday - Area B": {"address": "61 Timms Avenue, KILSYTH 3137"}, # Friday - Area B
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        entries = []

        #initiate a session
        url = "https://enterprise.mapimage.net/IntraMaps99/ApplicationEngine/Projects/"

        payload={}
        params = {
            "configId": "5bb5b19d-9071-475e-8139-c1402a12a785",
            "appType": "MapBuilder",
            "project": "e904c13a-b8da-41eb-b08f-20abc430a72a",
            "datasetCode": ""
        }
        headers = {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        sessionid = response.headers['X-IntraMaps-Session']



        #Load the Map Project (further requests don't appear to work if this request is not made)
        url = "https://enterprise.mapimage.net/IntraMaps99/ApplicationEngine/Modules/"

        payload = json.dumps({
          "module": "d41bec46-67ad-4f32-bcde-cebb62dce275"
        })

        params = {
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)



        #search for the address
        url = "https://enterprise.mapimage.net/IntraMaps99/ApplicationEngine/Search/"

        payload = json.dumps({
          "fields": [
            self._address
          ]
        })

        params = {
            "infoPanelWidth": "0",
            "mode": "Refresh",
            "form": "1a33b2ba-5075-4224-9784-47a1f1478c0a",
            "resubmit": "false",
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        #this request may return multiple addresses. Use the first one.
        address_map_key = response.json()
        address_map_key = address_map_key['fullText'][0]['mapKey']



        #Lookup the specific property data
        url = "https://enterprise.mapimage.net/IntraMaps99/ApplicationEngine/Search/Refine/Set"

        payload = json.dumps({
          "selectionLayer": "4c3fc44c-4cd2-40ca-8e4d-da2b8765ed68",
          "mapKey": address_map_key,
          "mode": "Refresh",
          "dbKey": address_map_key,
          "zoomType": "current"
        })

        params = {
            "IntraMapsSession": sessionid
        }

        response = requests.request("POST", url, headers=headers, data=payload, params=params)
        response = response.json()

        # Rubbish (green lid) - Happens on each recyclables and garden organics

        # Recyclables (blue lid)
        recyclables_date_text = response['infoPanels']['info1']['feature']['fields'][2]['value']['value']
        recyclables_date = datetime.strptime(recyclables_date_text,"%A, %d %b %Y").date()
        entries.append(
            Collection(
                recyclables_date,"Recyclables","mdi:recycle"
            )
        )
        entries.append(
            Collection(
                recyclables_date,"Garbage"
            )
        )

        # Garden Organics (maroon lid)
        garden_organics_date_text = response['infoPanels']['info1']['feature']['fields'][3]['value']['value']
        garden_organics_date = datetime.strptime(garden_organics_date_text,"%A, %d %b %Y").date()
        entries.append(
            Collection(
                garden_organics_date,"Garden Organics","mdi:leaf"
            )
        )
        entries.append(
            Collection(
                garden_organics_date,"Garbage"
            )
        )


        return entries