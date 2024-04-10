import datetime as dt
import json
import logging
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "The Hawkesbury City Council, Sydney"
DESCRIPTION = "Source for Hawkesbury City Council, Sydney, Australia waste collection."
URL = "https://www.hawkesbury.nsw.gov.au/"
TEST_CASES = {
    "south windsor, 539a George Street": {
        "suburb": "south windsor",
        "street": "George Street",
        "houseNo": 539,
    },
    "Windsor, catherine street 7": {
        "suburb": "Windsor",
        "street": "catherine st",
        "houseNo": 7,
    },
    "Kurrajong, Bells Line Of Road 1052 ": {
        "suburb": "Kurrajong HILLS",
        "street": "Bells Line Of Road",
        "houseNo": 1052,
    }
}
API_URL = "https://data.hawkesbury.nsw.gov.au/api"
_LOGGER = logging.getLogger(__name__)
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}
STREETNAMES = {
    "Av": "Avenue",
    "Cct": "Circuit",
    "Cr": "Crescent",
    "Ct": "Court",
    "Dr": "Drive",
    "Esp": "Esplanade",
    "Gr": "Grove",
    "Hts": "Heights",
    "Hwy": "Highway",
    "Pde": "Parade",
    "Pl": "Place",
    "Rd": "Road",
    "St": "Street",
    "Tce": "Terrace",
}


class Source:
    def __init__(self, suburb, street, houseNo):
        self._suburb = suburb.upper()
        self._street = street
        self._houseNo = str(houseNo)
        self._url = API_URL

    def get_data(self, bin_prefix: str, fields) -> list[Collection]:
        entries: list[Collection] = []

        frequency = int(fields.get(f'{bin_prefix}_schedule'))
        if frequency == 0:
            return entries

        base_string = fields.get(f'{bin_prefix}_week1', dt.datetime.min.strftime('%Y-%m-%d'))
        basedate = dt.datetime.strptime(base_string, "%Y-%m-%d")

        # Get number of days between basedate and a year from now
        days = ((dt.datetime.now() + dt.timedelta(days=365)) - basedate).days

        date_list = [basedate + dt.timedelta(days=x) for x in range(0, days, frequency)]
        name = bin_prefix.replace("bin", "").title()
        for dateStr in date_list:
            entries.append(Collection(dateStr.date(), name, ICON_MAP.get(name.upper())))
        return entries


    def fetch(self):
        # check address values are not abbreviated
        address = self._street
        for key in STREETNAMES.keys():
            regex = r"\b{}\b".format(key.lower())
            address = re.sub(
                pattern=regex,
                repl=STREETNAMES[key],
                string=address.lower())

        # get list of suburbs
        r = requests.get(
            f"{self._url}/records/1.0/search/?sort=gisaddress&refine.gisaddress={self._houseNo} {address.title()} {self._suburb}&rows=1&dataset=bin-collection-days&timezone=Australia/Sydney&lang=en")
        data = json.loads(r.text)

        if len(data['records']) == 0:
            raise Exception(f"house not found: {self._houseNo}")
        
        # get collection schedule
        record = data['records']
        garbagebin_entries = self.get_data('garbagebin', record['fields'])
        recyclebin_entries = self.get_data('recyclebin', record['fields'])
        organicbin_entries = self.get_data('organicbin', record['fields'])
        entries = garbagebin_entries + recyclebin_entries + organicbin_entries

        return entries
       
