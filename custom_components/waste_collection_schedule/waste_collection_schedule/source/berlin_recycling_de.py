import json
from datetime import datetime
import logging

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

LOGGER = logging.getLogger(__name__)

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
        r = session.post(SERVICE_URL+"Login.aspx/Auth", json=args)
        LOGGER.debug("login response: %s", r.text)
        r.raise_for_status()
        serviceUrl = SERVICE_URL + "Default.aspx"
        
        
        headers = {
                'Content-Type': 'application/json'
        }

        r = session.post(serviceUrl + "/GetDashboard", headers=headers)
        LOGGER.debug("dashboard response: %s", r.text)
        r.raise_for_status()

        request_data = {
            "datasettablecode": "ABFUHRKALENDER",
            "startindex": 0,
            "searchtext": "",
            "rangefilter": "[]",
            "ordername": "",
            "orderdir": "",
            "ClientParameters": "",
            "headrecid": "",
        }
        r = session.post(serviceUrl + "/GetDatasetTableHead", json=request_data, headers=headers)
        LOGGER.debug("data response: %s", r.text)
        

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
