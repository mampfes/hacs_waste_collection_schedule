import logging
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfall Neunkirchen Siegerland"
DESCRIPTION = " Source for 'Abfallkalender Neunkirchen Siegerland'."
URL = "https://www.neunkirchen-siegerland.de"
TEST_CASES = {
    "Waldstraße":{ "street":"Waldstr"}
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, strasse):
        self._strasse = strasse
        self._ics = ICS()

    def fetch(self):

        args = {"out":"json", "type": "abto", "select":"2", "refid": "3362.1", "term": self._strasse }
        header = {"referer": "https://www.neunkirchen-siegerland.de"}
        r = requests.get("https://www.neunkirchen-siegerland.de/output/autocomplete.php", params=args,headers=header)

        if r.status_code != 200:
            _LOGGER.error("Error querying calender data")
            return []

        ids = r.json()

        if len(ids) == 0:
            raise Exception("no address found")

        if len(ids) > 1:
            raise Exception (" to many addresses found, specify more detailed street name")

        args = {"ModID":48, "call": "ical", "pois": ids[0][0], "kat": 1, "alarm":0}
        r = requests.get("https://www.neunkirchen-siegerland.de/output/options.php", params=args,headers=header)

        if r.status_code != 200:
            _LOGGER.error("Error querying calender data")
            return []

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0],d[1]))

        return entries
