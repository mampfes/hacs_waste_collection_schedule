import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SRV Återvinning"
DESCRIPTION = "Source for SRV återvinning AB, Sweden"
URL = "https://www.srvatervinning.se"
TEST_CASES = {
    "Skansvägen": {"address": "Skansvägen"},
    # "Test1": {"address": "tun"}, not working anymore after api endpoint change
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
        r = requests.get(
            "https://www.srvatervinning.se/rest-api/core/sewagePickup/search", params
        )
        r.raise_for_status()

        data = r.json()

        entries = []

        for container in data["results"][0]["containers"]:
            type = container["contentType"]
            for calentry in container["calendars"]:
                date_obj = datetime.strptime(calentry["startDate"], "%Y-%m-%d").date()
                entries.append(Collection(date_obj, type))

        return entries
