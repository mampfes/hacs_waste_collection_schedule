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
            "x-secret": "8eTFgy3AQH0mzAcj3xMwaKnNyNnijEFIEegjgNpBHifqtQ4IEyWqmJGFz3ggKQ7B4vwUYS8xz8KwACZihCmboGb6brtVB3rpne2Ww5uUM2n3i4SKNUg6Vp7lhAS8INDUNH8Ll7WPhWRsQOXBCjVz5H8fr0q6fqZCosXdndbNeiNy73FqJBn794qKuUAPTFj8CuAbwI6Wom98g72Px1MPRYHwyrlHUbCijmDmA2zoWikn34LNTUZPd7kS0uuFkibkLxCc1PeOVYVHeh1xVxxwGBsMINWJEUiIBqZt9VybcHpUJTYzureqfund1aeJvmsUjwyOMhLSxj9MLQ07iTbvzQa6vbJdC0hTsqTlndccBRm9lkxzNpzJBPw8VpYSyS3AhaR2U1n4COZaJyFfUQ3LUBzdj5gV8QGVGCHMlvGJM0ThnRKENSWZLVZoHHeCBOkfgzp0xl0qnDtR8eJF0vLkFiKwjX7DImGoA8IjqOYygV3W9i9rIOfK",
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
