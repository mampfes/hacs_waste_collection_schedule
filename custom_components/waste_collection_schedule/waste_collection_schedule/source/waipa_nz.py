import datetime
from waste_collection_schedule import Collection

import requests
import json
from datetime import datetime

TITLE = "Waipa District Council"
DESCRIPTION = "Source for Waipa District Council. Finds both general and glass recycling dates."
URL = "https://www.waipadc.govt.nz/"
TEST_CASES = {
    "10 Queen Street": {"address": "10 Queen Street"} #Monday
    ,"1 Acacia Avenue": {"address": "1 Acacia Avenue"}#Wednesday
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        entries = []

        #initiate a session
        url = "https://enterprise.mapimage.net/IntraMaps22A/ApplicationEngine/Projects/?configId=6aa41407-1db8-44e1-8487-0b9a08965283&appType=MapBuilder&project=b5bc138e-edce-4b01-b159-ec44539ab455&datasetCode="

        payload={}
        headers = {
          'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
          'Accept': '*/*',
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'sec-ch-ua-mobile': '?0',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        sessionid = response.headers['X-IntraMaps-Session']



        #Load the Map Project (further requests don't appear to work if this request is not made)
        url = "https://enterprise.mapimage.net/IntraMaps22A/ApplicationEngine/Modules/?IntraMapsSession=" + sessionid
        print(url)
        print()
        print()

        payload = json.dumps({
          "module": "5373c4e1-c975-4c8f-b51a-0ac976f5313c",
          "includeWktInSelection": True,
          "includeBasemaps": False
        })
        headers = {
          'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
          'Accept': '*/*',
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'sec-ch-ua-mobile': '?0',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"'
        }

        response = requests.request("POST", url, headers=headers, data=payload)



        #search for the address
        url = "https://enterprise.mapimage.net/IntraMaps22A/ApplicationEngine/Search/?infoPanelWidth=0&mode=Refresh&form=e6677a33-9d47-407a-b199-5c7967a4be07&resubmit=false&IntraMapsSession=" + sessionid

        payload = json.dumps({
          "fields": [
            self._address
          ]
        })
        headers = {
          'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
          'Accept': '*/*',
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'sec-ch-ua-mobile': '?0',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        #this request may return multiple addresses. Use the first one.
        address_map_key = response.json()
        address_map_key = address_map_key['fullText'][0]['mapKey']



        #Lookup the specific property data
        url = "https://enterprise.mapimage.net/IntraMaps22A/ApplicationEngine/Search/Refine/Set?IntraMapsSession=" + sessionid

        payload = json.dumps({
          "selectionLayer": "e7163a17-2f10-42b1-8dbf-8c53adf089a8",
          "mapKey": address_map_key,
          "infoPanelWidth": 350,
          "mode": "Refresh",
          "dbKey": address_map_key,
          "zoomType": "current"
        })
        headers = {
          'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
          'Accept': '*/*',
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'sec-ch-ua-mobile': '?0',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
          'sec-ch-ua-platform': '"Windows"'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()

        #general recycling (yellow lid)
        general_recycling_dates_text = response['infoPanels']['info1']['feature']['fields'][3]['value']['value']
        entries.append(
            Collection(
                datetime.strptime(general_recycling_dates_text.split(" ")[4][:-1],"%d-%b-%Y").date()
                ,"Recycling"
            )
        )
        entries.append(
            Collection(
                datetime.strptime(general_recycling_dates_text.split(" ")[-1],"%d-%b-%Y").date()
                ,"Recycling"
            )
        )

        #glass recycling (blue lid)
        glass_recycling_dates_text = response['infoPanels']['info1']['feature']['fields'][4]['value']['value']
        entries.append(
            Collection(
                datetime.strptime(glass_recycling_dates_text.split(" ")[4][:-1],"%d-%b-%Y").date()
                ,"Glass"
            )
        )
        entries.append(
            Collection(
                datetime.strptime(glass_recycling_dates_text.split(" ")[-1],"%d-%b-%Y").date()
                ,"Glass"
            )
        )

        return entries
