import logging
import requests
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "SRV, Sweden"
DESCRIPTION = "Source for SRV, Sweden"
URL = "https://www.srvatervinning.se/sophamtning/privat/hamtinformation-och-driftstorningar"
TEST_CASES = {
  "Skansvägen" : {"address":"Skansvägen" },
  "TEST2" : {"address":"tun" }
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):

        r = requests.get('https://www.srvatervinning.se/rest-api/srv-slamsok-rest-new/search?query='+self._address+'&city=')

        if r.status_code != 200:
            _LOGGER.error("Error querying calender data")
            return []

        data = r.json()

        entries = []

        for container in data["results"][0]["containers"]:
            type=container["contentType"]
            for calentry in container["calendars"]:
                dates =  {calentry["startDate"],type}
                date_obj = datetime.strptime(calentry["startDate"], '%Y-%m-%d').date()
                entries.append(Collection(date_obj,type))

        return entries