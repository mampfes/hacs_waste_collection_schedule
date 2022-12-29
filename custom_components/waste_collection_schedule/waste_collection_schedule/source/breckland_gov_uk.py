import logging
import requests
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Breckland Council, UK"
DESCRIPTION = "Source for breckland.gov.uk"
URL = "https://www.breckland.gov.uk/mybreckland"
TEST_CASES = {
  "test1" : {"postcode":"IP22 2LJ","address":"glen travis" },
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self,postcode,address):
        self._postcode = postcode
        self._address = address

    def fetch(self):

        json_data = {
            "jsonrpc":"2.0",
             "id":"",
             "method":"Breckland.Whitespace.JointWasteAPI.GetSiteIDsByPostcode",
             "params":{
                 "postcode":self._postcode,
                 "environment":"live"
                 }
             }

        headers = {'referer': 'https://www.breckland.gov.uk/mybreckland'}
        url = 'https://www.breckland.gov.uk/apiserver/ajaxlibrary'
        r = requests.post(url, json=json_data,headers=headers)

        if r.status_code != 200:
            _LOGGER.error("Error querying calender data")
            return []

        json_response = r.json()

        uprn = ""
        for key in json_response['result']:
            if self._address.lower() in key['name'].lower():
                uprn = (key['uprn'])

        if uprn == "":
            _LOGGER.error("Error querying calender data")
            return []

        json_data = {
            "jsonrpc":"2.0",
            "id":"",
            "method":"Breckland.Whitespace.JointWasteAPI.GetBinCollectionsByUprn",
            "params":{
                "uprn":uprn,
                "environment":"live"
                }
            }

        r = requests.post(url, json=json_data,headers=headers)

        if r.status_code != 200:
            _LOGGER.error("Error querying calender data")
            return []

        waste = r.json()
        waste = waste['result']

        entries = []

        for data in waste:
            print(data['collectiontype'])
            print(data['nextcollection'])
            entries.append(Collection(datetime.strptime(data['nextcollection'],'%d/%m/%Y %H:%M:%S').date(),data['collectiontype']))

        return entries