import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Berlin Recycling"
DESCRIPTION = "Source for Berlin Recycling waste collection."
URL = "https://berlin-recycling.de"
TEST_CASES = {
    "Germanenstrasse": {
        "username": "!secret berlin_recycling_username",
        "password": "!secret berlin_recycling_password",
    },
}

SERVICE_URL = "https://kundenportal.berlin-recycling.de/"


class Source:
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def fetch(self):
        session = requests.session()

        # first get returns session specific url
        r = session.get(SERVICE_URL, allow_redirects=False)
        r.raise_for_status()

        # get session id's

        args = {
            "username": self._username,
            "password": self._password,
            "rememberMe": False,
            "encrypted": False,
        }

        # login
        r = session.post(SERVICE_URL+"Login.aspx/Auth", data=args)
        r.raise_for_status()
        serviceUrl = SERVICE_URL + "Default.aspx/"

        request_data = {"withhtml": "true"}
        r = session.post(serviceUrl + "/GetDashboard", json=request_data)
        r.raise_for_status()

        request_data = {"datasettable": "ENWIS_ABFUHRKALENDER"}
        r = session.post(serviceUrl + "/ChangeDatasetTable", json=request_data)
        r.raise_for_status()

        request_data = {
            "datasettablecode": "ENWIS_ABFUHRKALENDER",
            "startindex": 0,
            "searchtext": "",
            "rangefilter": "",
            "ordername": "",
            "orderdir": "",
            "ClientParameters": "",
            "headrecid": "",
        }
        r = session.post(serviceUrl + "/GetDatasetTableHead", json=request_data)

        data = json.loads(r.text)
        # load json again, because response is double coded
        data = json.loads(data["d"])

        entries = []
        for d in data["data"]:
            date = datetime.strptime(d["Task Date"], "%Y-%m-%d").date()
            entries.append(Collection(date, d["Material Description"]))
        return entries
