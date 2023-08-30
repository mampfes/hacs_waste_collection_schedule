import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "IRiS"
DESCRIPTION = "Source for IRiS."
URL = "https://www.iris-salten.no"
TEST_CASES = {
    "Alsosgården 11, bodø": {"address": "Alsosgården 11", "kommune": "bodø"},
    "Kalnesveien 3, Fauske kommune": {
        "address": "kAlnesveien 3",
        "kommune": "fAuske kommune",
    },
}


ICON_MAP = {
    "generalwaste": "mdi:trash-can",
    "glass_metal": "mdi:bottle-soda",
    "food": "mdi:food-apple",
    "paper": "mdi:package-variant",
    "plastic": "mdi:recycle",
}


API_URL = "https://www.iris-salten.no/tommekalender/"


class Source:
    def __init__(self, address: str, kommune: str):
        self._address: str = address.lower().strip()
        self._kommune: str = kommune.lower().strip()

    def fetch(self):
        s = requests.Session()
        r = s.get(
            "https://www.iris-salten.no/xmlhttprequest.php",
            params={"service": "irisapi.realestates", "address": self._address},
        )
        r.raise_for_status()
        responses = r.json()
        if len(responses) == 0:
            raise ValueError("No address found")
        if len(responses) == 1:
            response = responses[0]
        else:
            response = responses[0]
            for r in responses:
                if self._kommune in r["kommune"] or r["kommune"] in self._kommune:
                    response = r
                    break

        r = s.get(
            "https://www.iris-salten.no/xmlhttprequest.php",
            params={
                "service": "irisapi.setestate",
                "estateid": response["id"],
                "estatename": response["adresse"],
                "estatemunicipality": response["kommune"],
            },
        )
        r.raise_for_status()
        r = s.get(
            "https://www.iris-salten.no/xmlhttprequest.php?service=irisapi.estateempty"
        )
        r.raise_for_status()

        entries = []
        for d in r.json()["days"]:
            date = datetime.datetime.strptime(d["date"], "%Y-%m-%d").date()
            for event in d["events"]:
                icon = ICON_MAP.get(event["fractionIcon"])  # Collection icon
                type = event["fractionName"]
                entries.append(Collection(date=date, t=type, icon=icon))

        return entries
