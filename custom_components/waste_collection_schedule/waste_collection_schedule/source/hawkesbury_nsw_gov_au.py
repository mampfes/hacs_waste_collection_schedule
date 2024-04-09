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
        "houseNo": "539",
    },
    "Windsor, catherine street 7": {
        "suburb": "Windsor",
        "street": "catherine street",
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


def fun(date):
    if date < dt.datetime.today():
        return False
    else:
        return True


class Source:
    def __init__(self, suburb, street, houseNo):
        self._suburb = suburb.upper()
        self._street = street
        self._houseNo = str(houseNo)
        self._url = API_URL

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
        entries = []
        entry = data['records'][-1]

        base_string = entry['fields'].get('garbagebin_week1', dt.datetime.min.strftime('%Y-%m-%d'))
        basedate = dt.datetime.strptime(base_string, "%Y-%m-%d")
        date_list = filter(fun, [basedate + dt.timedelta(weeks=x) for x in range(0, 52, 1)])
        name = 'Garbage'
        for dateStr in date_list:
            entries.append(Collection(dateStr.date(), name, ICON_MAP['DOMESTIC']))

        base_string = entry['fields'].get('recyclebin_week1', dt.datetime.min.strftime('%Y-%m-%d'))
        basedate = dt.datetime.strptime(base_string, "%Y-%m-%d")
        date_list = filter(fun, [basedate + dt.timedelta(weeks=x) for x in range(0, 52, 2)])
        name = 'Recycle'
        for dateStr in date_list:
            entries.append(Collection(dateStr.date(), name, ICON_MAP['RECYCLE']))

        base_string = entry['fields'].get('organicbin_week1', dt.datetime.min.strftime('%Y-%m-%d'))
        basedate = dt.datetime.strptime(base_string, "%Y-%m-%d")
        date_list = filter(fun, [basedate + dt.timedelta(weeks=x) for x in range(0, 52, 2)])
        name = 'Organic Bin'
        for dateStr in date_list:
            entries.append(Collection(dateStr.date(), name, ICON_MAP['ORGANIC']))
        return entries
