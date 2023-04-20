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
        r = session.post(f"{SERVICE_URL}Login.aspx/Auth", json=args)
        r.raise_for_status()
        serviceUrl = f"{SERVICE_URL}Default.aspx"

        # get the default view (might not needed, but is a good check the login worked)
        response = session.get('https://kundenportal.berlin-recycling.de/Default.aspx')
        if response.history:
            raise Exception ('The default view request was redirected to ' + response.url)
        
        headers = {
                'Content-Type': 'application/json'
        }

        r = session.post(f"{serviceUrl}/GetDashboard", headers=headers)
        r.raise_for_status()

        request_data = {
            "datasettablecode": "ABFUHRKALENDER",
            "startindex": 0,
            "searchtext": "",
            "rangefilter": "[]",
            "ordername": "",
            "orderdir": "",
            "ClientParameters": "",
            "headrecid": ""
        }
        r = session.post(f"{serviceUrl}/GetDatasetTableHead", json=request_data, headers=headers)

        data = json.loads(r.text)
        # load json again, because response is double coded
        data = json.loads(data["d"])

        entries = []
        if "Object" not in data or "data" not in data["Object"]:
            raise Exception("No data found", data)
        
        for d in data["Object"]["data"]:
            date = datetime.strptime(d["Task Date"], "%Y-%m-%d").date()
            entries.append(Collection(date, d["Material Description"]))
        return entries
