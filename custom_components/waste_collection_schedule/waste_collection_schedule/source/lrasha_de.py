import datetime
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS


TITLE = "Landkreis Schwäbisch Hall"
DESCRIPTION = "Source for lrasha.de - Landkreis Schwäbisch Hall"
URL = "https://www.lrasha.de"
TEST_CASES = {
    "Ilshofen": {"location": "68345"}
}

API_URL = "http://api.cross-7.de/public/calendar/396/events/ics?SecondCategoryIds="
HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(self, location):
        self._location = location
        self._ics = ICS()

    def fetch(self):
        # get ics file
        full_url = API_URL + str(self._location)
        r = requests.get(full_url, headers=HEADERS)
        r.raise_for_status()

        # parse ics file
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
