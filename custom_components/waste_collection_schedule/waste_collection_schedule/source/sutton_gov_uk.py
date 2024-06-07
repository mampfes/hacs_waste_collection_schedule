from time import sleep

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Sutton Council, London"
DESCRIPTION = "Source for Sutton Council, London."
URL = "https://sutton.gov.uk"
TEST_CASES = {"4721996": {"id": 4721996}, "4499298": {"id": "4499298"}}


ICON_MAP = {
    "non-recyclable": "mdi:trash-can",
    "paper": "mdi:package-variant",
    "mixed": "mdi:recycle",
    "food": "mdi:food",
}


API_URL = "https://waste-services.sutton.gov.uk/waste/{id}"
ICAL_URL = API_URL + "/calendar.ics"


class Source:
    def __init__(self, id: str | int):
        self._id: str | int = id
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        api_url = API_URL.format(id=self._id)
        ical_url = ICAL_URL.format(id=self._id)

        r = s.get(api_url)
        while f'hx-get="/waste/{self._id}"' in r.text:
            sleep(2)
            r = s.get(api_url)
        r.raise_for_status()

        r = s.get(ical_url)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(
                Collection(d[0], d[1], ICON_MAP.get(d[1].split(" ")[0].lower()))
            )

        return entries
