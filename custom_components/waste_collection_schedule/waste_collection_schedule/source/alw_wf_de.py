import datetime
import json

import pytz
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Abfallwirtschaft Landkreis Wolfenbüttel"
DESCRIPTION = "Source for ALW Wolfenbüttel."
URL = "https://alw-wf.de"
TEST_CASES = {
    "Linden alte Straße": {"ort": "Linden mit Okertalsiedlung", "strasse": "Siedlung"},
    "Linden neuere Straße": {
        "ort": "Linden mit Okertalsiedlung",
        "strasse": "Kleingartenweg",
    },
    "Dettum": {"ort": "Dettum", "strasse": "Egal!"},
}

API_URL = "https://abfallapp.alw-wf.de"
AUTH_DATA = {
    "auth": {
        "Name": "ALW",
        "Version": "2.0",
        "AuthKey": "ALW",
        "DeviceID": "ALW",
        "Username": "ALW",
        "Password": "ALW",
    },
    "request": {},
}
ALL_STREETS = "Alle Straßen"
BIN_TYPE_NORMAL = "0"


class Source:
    def __init__(self, ort, strasse):
        self._ort = ort
        self._strasse = strasse

    def fetch(self):
        auth_params = json.dumps(AUTH_DATA)

        # ALW WF uses a self-signed certificate so we need to disable certificate verification
        r = requests.post(f"{API_URL}/GetOrte.php", data=auth_params, verify=False)
        orte = r.json()
        if orte["result"][0]["StatusCode"] != 200:
            raise Exception(f"Error getting Orte: {orte['result'][0]['StatusMsg']}")

        orte = orte["result"][0]["result"]
        orte = {i["Name"]: i["ID"] for i in orte}
        ort_id = orte.get(self._ort, None)

        if ort_id is None:
            raise Exception(f"Error finding Ort {self._ort}")

        r = requests.post(f"{API_URL}/GetStrassen.php", data=auth_params, verify=False)
        strassen = r.json()
        if strassen["result"][0]["StatusCode"] != 200:
            raise Exception(
                f"Error getting Straßen: {strassen['result'][0]['StatusMsg']}"
            )

        strassen = strassen["result"][0]["result"]
        strasse_id = None
        for strasse in strassen:
            if strasse["OrtID"] != ort_id:
                continue
            if strasse["Name"] == ALL_STREETS or strasse["Name"] == self._strasse:
                strasse_id = strasse["ID"]
                break
            continue

        if strasse_id is None:
            raise Exception(f"Error finding Straße {self._strasse}")

        r = requests.post(f"{API_URL}/GetArten.php", data=auth_params, verify=False)
        arten = r.json()
        if arten["result"][0]["StatusCode"] != 200:
            raise Exception(f"Error getting Arten: {arten['result'][0]['StatusMsg']}")

        arten = arten["result"][0]["result"]
        arten = [i for i in arten if i["Art"] == BIN_TYPE_NORMAL]
        arten = {int(i["Wertigkeit"]): i["Name"] for i in arten}

        entries = []
        r = requests.post(
            f"{API_URL}/GetTermine.php/{strasse_id}", data=auth_params, verify=False
        )
        termine = r.json()
        if termine["result"][0]["StatusCode"] != 200:
            raise Exception(
                f"Error getting Termine: {termine['result'][0]['StatusMsg']}"
            )

        termine = termine["result"][0]["result"]
        for termin in termine:
            ts = int(termin["DatumLong"]) / 1000
            # Timestamps are unix with milliseconds but not UTC...
            date = datetime.datetime.fromtimestamp(
                ts, tz=pytz.timezone("Europe/Berlin")
            ).date()
            types = int(termin["Abfallwert"])
            for art in arten:
                if types & art:
                    entries.append(Collection(date, arten[art]))

        return entries
