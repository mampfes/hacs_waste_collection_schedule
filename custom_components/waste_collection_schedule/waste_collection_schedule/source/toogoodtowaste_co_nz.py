import datetime
import json
import time

from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

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
        self._session = requests.Session(impersonate="chrome124")
        self._session.headers.update({"Referer": URL})

    def fetch(self):
        ts = round(time.time() * 1000)
        try:
            # Warm up the browser session so Cloudflare/session cookies are set before API access.
            warmup_response = self._session.get(URL, timeout=30)
            warmup_response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError("Failed to initialize toogoodtowaste API session.") from e

        try:
            r = self._session.get(
                f"{URL}_designs/integrations/address-finder/addressdata.json",
                params={"query": self._address, "timestamp": ts},
                timeout=30,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            raise ValueError("Failed to fetch toogoodtowaste address data.") from e
        try:
            data = r.json()
        except json.JSONDecodeError as e:
            raise ValueError(
                "Failed to decode address finder response. This may indicate bot protection."
            ) from e

        filtered = [
            res["attributes"]
            for res in data
            if res["attributes"]["address"] == self._address
        ]
        if len(filtered) == 0:
            raise SourceArgumentNotFound("address", self._address)
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
