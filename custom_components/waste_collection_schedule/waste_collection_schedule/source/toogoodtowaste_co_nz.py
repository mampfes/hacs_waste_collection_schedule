import datetime
import json
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hutt City Council"
DESCRIPTION = "Source for Hutt City Council."
URL = "https://www.toogoodtowaste.co.nz/"
TEST_CASES = {
    "Bus Barns": {"address": "493 Muritai Road EASTBOURNE"},  # Monday
    "Council": {"address": "30 Laings Road HUTT CENTRAL"},  # Tuesday
}

WASTE_TYPE_MAP = {
    "red": "Red bin",
    "yellow": "Yellow bin",
    "blue": "Blue crate",
    "green": "Green waste bin",
}

ICON_MAP = {
    "red": "mdi:trash-can",
    "yellow": "mdi:recycle",
    "blue": "mdi:glass-fragile",
    "green": "mdi:tree",
}

PICTURE_MAP = {
    "red": f"{URL}__data/assets/image/0024/1779/bin-red.png",
    "yellow": f"{URL}__data/assets/image/0017/1781/bin-yellow.png",
    "blue": f"{URL}__data/assets/image/0016/1780/bin-blue.png",
    "green": f"{URL}__data/assets/image/0018/1782/bin-green.png",
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        ts = round(time.time() * 1000)
        encoded_address = requests.utils.quote(self._address)
        url = f"{URL}_designs/integrations/address-finder/addressdata.json?query={encoded_address}&timestamp={ts}"
        r = requests.get(url)
        data = json.loads(r.text)

        filtered = [
            res["attributes"]
            for res in data
            if res["attributes"]["address"] == self._address
        ]
        if len(filtered) == 0:
            raise Exception(f"No result found for address {self._address}")
        if len(filtered) > 1:
            raise Exception(
                f"More then one result returned for address {self._address}."
            )

        result = filtered[0]
        bin_list = json.loads(result["bin_list"])

        entries = []
        for bin in bin_list:
            entries.append(
                Collection(
                    datetime.date(*map(int, result["next_collection_date"].split("-"))),
                    WASTE_TYPE_MAP.get(bin, bin),
                    picture=PICTURE_MAP.get(bin),
                    icon=ICON_MAP.get(bin),
                )
            )

        return entries
