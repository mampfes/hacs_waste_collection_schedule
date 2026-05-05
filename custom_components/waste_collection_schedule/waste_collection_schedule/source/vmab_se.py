import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup as bs
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Västblekinge Miljö AB (VMAB), Blekinge Sweden
#
# The public URL is https://vmab.se/privat/vmabs-tomningskalender
# However, this uses an iframe from https://cal.vmab.se/ which is the
# actual service providing the bin data.
#
# One first has to do a search since they put an ID in the list of
# search results which is required when sending the request to get the
# bin data. The data then comes injected into a script tag as it's
# normally used to build a browsable calendar for easy viewing.
#
# Bins in this municipality have four types of waste each, and each
# house has 2 bins, example raw data for the two bins:
#
# { title: 'Max 1, Mat, Brännbart, Färgat glas, Tidningar.', start: '2024-09-12' },
# { title: 'Max 2, Plast, Pappersförpackningar, Ofärgat glas, Metall.', start: '2024-09-05' },
#
# Note: This API does not apply for apartment buildings, municipal/state
# services or similar types of buildings as those do not have the same
# types of bins as regular houses.
#

TITLE = "VMAB"
DESCRIPTION = "Source for Västblekinge Miljö AB waste collection."
URL = "https://vmab.se"
TEST_CASES = {"Home": {"street_address": "Rosenborgsvägen 35, Karlshamn"}}

API_URL = "https://vmab.se/privat/vmabs-tomningskalender"


class Source:
    def __init__(self, street_address):
        addr_parts = street_address.split(",")
        self._street_address = addr_parts[0]
        self._city = addr_parts[1].lstrip()

    def fetch(self):
        data = {"search_address": self._street_address}
        headers = {
            "Accept-Encoding": "identity",
            "Accept": "*/*",
            "Accept-Language": "sv-SE,sv;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        response = requests.post(
            "https://cal.vmab.se/search_suggestions.php",
            data=data,
            headers=headers,
        )

        soup = bs(response.text, "html.parser")
        pickup_id = False
        for el_addr in soup.find_all("span", attrs={"class": "address"}):
            if el_addr.string == self._street_address:
                for el_addr_sib in el_addr.next_siblings:
                    if el_addr_sib.name == "span" and el_addr_sib.string == self._city:
                        pickup_id = el_addr.parent["id"]
                        break
                if pickup_id:
                    break
        if not pickup_id:
            return []

        data = {
            "chosen_address": f"{self._street_address} {self._city}",
            "chosen_address_pickupid": pickup_id,
        }
        response = requests.post(
            "https://cal.vmab.se/get_data.php",
            data=data,
            headers=headers,
        )

        entries = []
        for entry in re.findall(r"{.title:[^}]+}", response.text):
            json_entry = json.loads(
                re.sub(r"(title|start):", r'"\1":', entry.replace("'", '"'))
            )
            icon = "mdi:recycle"
            waste_type = json_entry["title"].split(",")[0].lstrip()
            pickup_date = datetime.fromisoformat(json_entry["start"]).date()
            entries.append(Collection(date=pickup_date, t=waste_type, icon=icon))
        return entries
