import requests
import datetime
import json
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Source for Jumomind.de based services."
URL = "https://www.jumomind.de"
TEST_CASES = OrderedDict(
    [
        ("ZAW", {"service_id": "zaw", "city_id": 106, "area_id": 94}),
        ("Bad Homburg", {"service_id": "hom", "city_id": 1, "area_id": 461}),
    ]
)


class Source:
    def __init__(self, service_id, city_id, area_id):
        self._service_id = service_id
        self._city_id = city_id
        self._area_id = area_id

    def fetch(self):
        args = {"r": "dates/0", "city_id": self._city_id, "area_id": self._area_id}

        # get json file
        r = requests.get(
            f"https://{self._service_id}.jumomind.com/mmapp/api.php", params=args
        )

        entries = []

        data = json.loads(r.text)
        for d in data:
            entries.append(
                CollectionAppointment(datetime.date.fromisoformat(d["day"]), d["title"])
            )

        return entries
