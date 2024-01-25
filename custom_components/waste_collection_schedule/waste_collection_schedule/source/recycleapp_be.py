import logging
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Recycle!"
DESCRIPTION = "Source for RecycleApp.be"
URL = "https://www.recycleapp.be"
TEST_CASES = {
    "1140 Evere, Bazellaan 1": {
        "postcode": 1140,
        "street": "Bazellaan",
        "house_number": 1,
    },
    "3001, Waversebaan 276 with events": {
        "postcode": 3001,
        "street": "Waversebaan",
        "house_number": 276,
    },
    "3001, Waversebaan 276 without events": {
        "postcode": 3001,
        "street": "Waversebaan",
        "house_number": 276,
        "add_events": False,
    },
    "1400, Rue de namur 1 with events": {
        "postcode": 1400,
        "street": "Rue de namur",
        "house_number": 1,
        "add_events": True,
    },
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, postcode, street, house_number, add_events=True):
        self._postcode = postcode
        self._street = street
        self._house_number = house_number
        self._add_events = add_events

    def fetch(self):
        url = "https://api.fostplus.be/recycle-public/app/v1"
        headers = {
            "x-secret": "Op2tDi2pBmh1wzeC5TaN2U3knZan7ATcfOQgxh4vqC0mDKmnPP2qzoQusmInpglfIkxx8SZrasBqi5zgMSvyHggK9j6xCQNQ8xwPFY2o03GCcQfcXVOyKsvGWLze7iwcfcgk2Ujpl0dmrt3hSJMCDqzAlvTrsvAEiaSzC9hKRwhijQAFHuFIhJssnHtDSB76vnFQeTCCvwVB27DjSVpDmq8fWQKEmjEncdLqIsRnfxLcOjGIVwX5V0LBntVbeiBvcjyKF2nQ08rIxqHHGXNJ6SbnAmTgsPTg7k6Ejqa7dVfTmGtEPdftezDbuEc8DdK66KDecqnxwOOPSJIN0zaJ6k2Ye2tgMSxxf16gxAmaOUqHS0i7dtG5PgPSINti3qlDdw6DTKEPni7X0rxM",
            "x-consumer": "recycleapp.be",
            "User-Agent": "",
            "Authorization": "",
        }
        r = requests.get(f"{url}/access-token", headers=headers)
        r.raise_for_status()
        headers["Authorization"] = r.json()["accessToken"]

        params = {"q": self._postcode}
        r = requests.get(f"{url}/zipcodes", params=params, headers=headers)
        r.raise_for_status()
        zipcodeId = r.json()["items"][0]["id"]

        params = {"q": self._street, "zipcodes": zipcodeId}
        r = requests.post(f"{url}/streets", params=params, headers=headers)
        r.raise_for_status()

        streetId = None
        for item in r.json()["items"]:
            if item["name"] == self._street:
                streetId = item["id"]
        if streetId is None:
            streetId = r.json()["items"][0]["id"]

        now = datetime.now()
        fromDate = now.strftime("%Y-%m-%d")
        untilDate = (now + timedelta(days=365)).strftime("%Y-%m-%d")
        params = {
            "zipcodeId": zipcodeId,
            "streetId": streetId,
            "houseNumber": self._house_number,
            "fromDate": fromDate,
            "untilDate": untilDate,
            #            "size":100,
        }
        r = requests.get(f"{url}/collections", params=params, headers=headers)
        r.raise_for_status()

        entries = []
        for item in r.json()["items"]:
            if "exception" in item and "replacedBy" in item["exception"]:
                continue

            date = datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%S.000Z").date()
            if item["type"] == "collection":
                entries.append(Collection(date, item["fraction"]["name"]["en"]))
            elif item["type"] == "event" and self._add_events:
                entries.append(Collection(date, item["event"]["title"]["en"]))

        return entries
