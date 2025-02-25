import logging
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

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
    "3200 Th. De Beckerstraat 1": {
        "postcode": 3200,
        "street": "Th. De Beckerstraat",
        "house_number": 1,
    },
    "9180 Lokeren, Abelendreef 1": {
        "postcode": 9180,
        "street": "Abelendreef",
        "house_number": 1,
    },
    "8700 Abeelstraat 1": {
        "postcode": 8700,
        "street": "Abeelstraat",
        "house_number": 1,
    },
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, postcode, street, house_number, add_events=True):
        self._postcode = postcode
        # Steet search does not work with . in the street name and with the chars in front of the .
        self._street = street
        self._steet_search = street.split(".")[-1]
        self._house_number = house_number
        self._add_events = add_events

    def fetch(self):
        url = "https://api.fostplus.be/recyclecms/app/v1"
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
        items = r.json()["items"]
        if len(items) == 0:
            raise SourceArgumentNotFound("postcode", self._postcode)

        for item in items:
            error = None
            if not item["available"]:
                continue
            zipcodeId = item["id"]
            try:
                entries = self._fetch_zipcode(zipcodeId, url, headers)
                if entries:
                    return entries
            except SourceArgumentNotFound as e:
                error = e

        if error:
            raise error
        raise Exception(
            "No data found for the postcode"
            + (", tired multiple zipcode, entries" if len(items) > 1 else "")
        )

    def _fetch_zipcode(
        self, zipcodeId: str, url: str, headers: dict[str, str]
    ) -> list[Collection]:
        params = {"q": self._steet_search, "zipcodes": zipcodeId}
        r = requests.post(f"{url}/streets", params=params, headers=headers)
        r.raise_for_status()

        streetId = None
        items = r.json()["items"]
        if len(items) == 0:
            raise SourceArgumentNotFound("street", self._street)
        for item in items:
            if item["name"].lower().strip() == self._street.lower().strip():
                streetId = item["id"]
        if streetId is None:
            _LOGGER.warning(
                f"No exact street match found, using first result: {r.json()['items'][0]['name']}"
            )
            streetId = items[0]["id"]

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
