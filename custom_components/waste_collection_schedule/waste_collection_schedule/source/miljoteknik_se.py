import json
import re
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Ronneby Miljöteknik, Blekinge Sweden
#
# The public URL is http://www.fyrfackronneby.se/hamtningskalender/
# However, this uses an iframe from http://35.228.122.136 which is the
# actual service providing the bin data.
#
# One first has to do a search since they put an ID in the list of
# search results which is required when sending the request to get the
# bin data. The data then comes injected into a script tag as it's
# normally used to build a browseable calendar for easy viewing.
#
# Bins in this municipality have four types of waste each, and each
# house has 2 bins, example raw data for the two bins:
#
# { title: 'Kärl 1 –  373 liter: Mat, Brännbart, färgat glas, tidningar.', start: '2023-09-12' },
# { title: 'Kärl 2 –  373 liter: Plast, pappersförpackningar, ofärgat glas, metall.', start: '2023-09-05' },
#
# The API will return about a years worth of bin collection dates
# and only the dates will change, title remains the same for the two
# bins. First one being Food, Burnables, Colored glass and Newspapers,
# and the second is Plastics, Cardboard, Non-colored glass and Metal.
#
# Note: This API does not apply for apartment buildings, municipal/state
# services or similar types of buildings as those do not have the same
# types of bins as regular houses. There is currently no known API for
# those bins, only for the so called "Fyrfack" bins (meaning four slots).
#

TITLE = "Ronneby Miljöteknik"
DESCRIPTION = "Source for Ronneby Miljöteknik waste collection."
URL = "http://www.fyrfackronneby.se"
TEST_CASES = {
    "Home": {"street_address": "Hjortsbergavägen 16, Johannishus"}
}

API_URL = "http://www.fyrfackronneby.se/hamtningskalender/"


class Source:
    def __init__(self, street_address):
        addr_parts = street_address.split(',')
        self._street_address = addr_parts[0]
        self._city = addr_parts[1].lstrip()

    def fetch(self):
        data = {"search_address": self._street_address}
        headers = {
            'Accept-Encoding': 'identity',
            'Accept': '*/*',
            'Accept-Language': 'sv-SE,sv;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        response = requests.post(
            "http://35.228.122.136/search_suggestions.php",
            data=data,
            headers=headers
        )

        soup = bs(response.text, 'html.parser')
        pickup_id = False
        for el_addr in soup.find_all('span', attrs={'class': 'address'}):
            if el_addr.string == self._street_address:
                for el_addr_sib in el_addr.next_siblings:
                    if el_addr_sib.name == 'span' and el_addr_sib.string == self._city:
                        pickup_id = el_addr.parent['id']
                        break
                if pickup_id:
                    break
        if not pickup_id:
            return []

        data = {
            "chosen_address": "{} {}".format(self._street_address, self._city),
            "chosen_address_pickupid": pickup_id
        }
        response = requests.post(
            "http://35.228.122.136/get_data.php",
            data=data,
            headers=headers
        )

        entries = []
        for entry in re.findall(r'{.title:[^}]+}', response.text):
            json_entry = json.loads(re.sub(r'(title|start):', r'"\1":', entry.replace("'", '"')))
            # Same icon always, due to two bins both being various recycled things
            icon = "mdi:recycle"
            waste_type = json_entry['title'].split(':')[1].lstrip()
            pickup_date = datetime.fromisoformat(json_entry['start']).date()
            entries.append(Collection(date=pickup_date, t=waste_type, icon=icon))
        return entries
