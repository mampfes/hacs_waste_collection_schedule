import logging
import requests
import urllib
from bs4 import BeautifulSoup
from datetime import date
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWB Oldenburg"
DESCRIPTION = "Source for 'Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)'."
URL = "https://www.oldenburg.de"
TEST_CASES = {
    "Polizeiinspektion Oldenburg": {"street": "Friedhofsweg", "house_number": 30}
}

API_URL = "https://www.oldenburg.de/startseite/leben-umwelt/awb/awb-von-a-bis-z/abfuhrkalender.html"

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = house_number
        self._ics = ICS(regex=r"(.*)\:\s*\!")

    def fetch(self):

        street_idx = self.get_street_idx(self._street)
        if street_idx == -1:
            _LOGGER.error("Error: Street not found..")
            return []
        year = date.today().year

        args = {
            "tx_collectioncalendar_abfuhrkalender[action]": "exportIcs",
            "tx_collectioncalendar_abfuhrkalender[controller]": "Frontend\Export",
            "tx_collectioncalendar_abfuhrkalender[houseNumber]": str(self._house_number).encode(
                "utf-8"
            ),
            "tx_collectioncalendar_abfuhrkalender[street]": str(street_idx).encode(
                "utf-8"
            ),
            "tx_collectioncalendar_abfuhrkalender[wasteTypes][1]": 1,
            "tx_collectioncalendar_abfuhrkalender[wasteTypes][2]": 2,
            "tx_collectioncalendar_abfuhrkalender[wasteTypes][3]": 3,
            "tx_collectioncalendar_abfuhrkalender[wasteTypes][4]": 4,
            "tx_collectioncalendar_abfuhrkalender[wasteTypes][5]": 5,
            "tx_collectioncalendar_abfuhrkalender[year]": year
        }

        # use '%20' instead of '+' in API_URL
        # https://stackoverflow.com/questions/21823965/use-20-instead-of-for-space-in-python-query-parameters
        args = urllib.parse.urlencode(args, quote_via=urllib.parse.quote)

        # post request
        r = requests.get(API_URL, params=args)

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries

    def get_street_mapping(self): # thanks @dt215git (https://github.com/mampfes/hacs_waste_collection_schedule/issues/539#issuecomment-1371413297)
        s = requests.Session()
        r = s.get(API_URL)

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("option")
        items = items[2:] # first two values are not street addresses so remove them

        streets = []
        ids = []
        for item in items:
            streets.append(item.text)  # street name
            ids.append(item.attrs["value"])  # dropdown value
        mapping = {k:v for (k,v) in zip(streets, ids)}

        return mapping

    def get_street_idx(self, street):
        mapping = self.get_street_mapping()

        for _street, idx in mapping.items():
            if _street == street:
                return idx

        return -1
