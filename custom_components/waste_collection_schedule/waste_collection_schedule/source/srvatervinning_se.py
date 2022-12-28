import logging
import requests
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "SRV Återvinning"
DESCRIPTION = "Source for SRV återvinning AB, Sweden"
URL = "https://www.srvatervinning.se"
TEST_CASES = {
  "Skansvägen" : {"address":"Skansvägen" },
  "TEST2" : {"address":"tun" }
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):

        params = {
            "query" : self._address,
            "city" : "",
        }
        url = 'https://www.srvatervinning.se/rest-api/srv-slamsok-rest-new/search'
        r = requests.get(url, params)

        if r.status_code != 200:
            _LOGGER.error("Error querying calender data")
            return []

        data = r.json()

        entries = []

        for container in data["results"][0]["containers"]:
            type=container["contentType"]
            for calentry in container["calendars"]:
                date_obj = datetime.strptime(calentry["startDate"], '%Y-%m-%d').date()
                entries.append(Collection(date_obj,type))

        return entries