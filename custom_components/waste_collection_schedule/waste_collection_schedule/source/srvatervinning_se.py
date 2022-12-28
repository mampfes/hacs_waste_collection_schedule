import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "SRV Återvinning"
DESCRIPTION = "Source for SRV återvinning AB, Sweden"
URL = "https://www.srvatervinning.se"
TEST_CASES = {
    "Skansvägen": {"address": "Skansvägen"},
    "Test1": {"address": "tun"},
    "Tullinge 1": {"address": "Hanvedens allé 78"},
    "Tullinge 2": {"address": "Skogsmulles Väg 22"},
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):

        params = {
            "query": self._address,
            "city": "",
        }
        url = "https://www.srvatervinning.se/rest-api/srv-slamsok-rest-new/search"
        r = requests.get(url, params)

        if r.status_code != 200:
            _LOGGER.error("Error querying calendar data")
            return []

        data = r.json()

        entries = []

        for container in data["results"][0]["containers"]:
            type = container["contentType"]
            for calentry in container["calendars"]:
                date_obj = datetime.strptime(calentry["startDate"], "%Y-%m-%d").date()
                entries.append(Collection(date_obj, type))

        return entries
