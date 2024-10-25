import json
import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Porirua City"
DESCRIPTION = "Source for Porirua City."
URL = "https://poriruacity.govt.nz/"
TEST_CASES = {
    "6 Ration Lane, Whitby, Porirua City 5024": {
        "address": "6 Ration Lane, Whitby, Porirua City 5024"
    },
    "104 Main Road, Titahi Bay, Porirua City 5022": {
        "address": "104 Main Road, Titahi Bay, Porirua City 5022"
    },
}


ICON_MAP = {
    "rubbish": "mdi:trash-can",
    "glass": "mdi:bottle-soda",
    "mixed": "mdi:recycle",
}


JS_URL = "https://storage.googleapis.com/pcc-wagtail-static-v4/pccapp/dist/assets/index.js?v=62120874e6b54e6e83ef020a2d376392"

ZONES_REGEX = re.compile(r"const\s?Xs\s?=\s?\{.*?\};", re.DOTALL)
COLLECTIONS_MAP_REGEX = re.compile(r"collections:\s?\{(\w+:\s?\[.*?\],?)+\}", re.DOTALL)


class Source:
    def __init__(self, address: str):
        self._address: str = address

    @staticmethod
    def get_js_infos() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        r = requests.get(JS_URL)
        zones_js_match = ZONES_REGEX.search(r.text)
        if not zones_js_match:
            raise Exception(
                "Zones not found probably due to a change in the websites javascript"
            )
        zones_js = zones_js_match.group(0)
        # const Xs={zone1:[new Date(2022,7,22),new Date(2022,7,23),new Date(2022,7,24),new Date(2022,7,25),new Date(2022,7,26)],zone2:[new Date(2022,7,8),new Date(2022,7,9),new Date(2022,7,10),new Date(2022,7,11),new Date(2022,7,12)],zone3:[new Date(2022,7,1),new Date(2022,7,2),new Date(2022,7,3),new Date(2022,7,4),new Date(2022,7,5)],zone4:[new Date(2022,7,15),new Date(2022,7,16),new Date(2022,7,17),new Date(2022,7,18),new Date(2022,7,19)]};
        zones_js = zones_js.replace("const Xs=", "").replace(";", "")
        # replace new Date(2022,7,22) with "2022-08-22"
        zones_js = re.sub(
            r"new Date\((\d{4}),(\d{1,2}),(\d{1,2})\)",
            lambda m: f'"{m.group(1)}-{str(int(m.group(2)) + 1).zfill(2)}-{m.group(3).zfill(2)}"',
            zones_js,
        )
        # replace zone1 with "zone1"
        zones_js = re.sub(r"zone(\d+)", r'"zone\1"', zones_js)
        ZONES: dict[str, list[str]] = json.loads(zones_js)
        collections_map_reg_result = COLLECTIONS_MAP_REGEX.search(r.text)
        if not collections_map_reg_result:
            raise Exception(
                "Collections map not found probably due to a change in the websites javascript"
            )
        collections_map_str = (
            collections_map_reg_result.group(0).replace("collections:", "").strip()
        )

        # repalce glass with "glass"
        collections_map_str = re.sub(r"(\w+):", r'"\1":', collections_map_str)
        COLLECTIONS_MAP: dict[str, list[str]] = json.loads(collections_map_str)
        return ZONES, COLLECTIONS_MAP

    def fetch(self) -> list[Collection]:
        ZONES, COLLECTIONS_MAP = self.get_js_infos()
        url = "https://maps.poriruacity.govt.nz/server/rest/services/Property/PropertyAdminExternal/MapServer/5/query"
        params: dict[str, str | int] = {
            "where": f"lower(address) = '{self._address.lower()}'",
            "f": "pjson",
            "outFields": "Address,OBJECTID,Collection_Day,Collection_Zone",
            "returnGeometry": "false",
            "resultRecordCount": 20,
            "orderByFields": "Address",
        }

        r = requests.get(url, params=params)

        data = r.json()
        if "features" not in data or not data["features"]:
            raise Exception(f"Address {self._address} not found")

        feature = data["features"][0]
        properties = feature["attributes"]

        today = date.today()

        col_day = properties["Collection_Day"]
        col_zone = properties["Collection_Zone"].replace(" ", "").lower()

        next_col_day = None
        for i in range(1, 8, 1):
            if (today + timedelta(days=i)).strftime("%A") == col_day:
                next_col_day = today + timedelta(days=i)
                break
        if not next_col_day:
            raise Exception(f"Collection day {col_day} not found")

        z = ZONES[col_zone][next_col_day.weekday()]

        z_date = datetime.strptime(z, "%Y-%m-%d")

        next_days = (
            next_col_day,
            next_col_day + timedelta(days=7),
            next_col_day + timedelta(days=14),
        )

        qs = ["glass", "rubbish", "mixed", "rubbish"]
        entries: list[Collection] = []
        for d in next_days:
            d_time = datetime(d.year, d.month, d.day)
            unix_time = int(d_time.timestamp() * 1000)
            z_date_unix_time = int(z_date.timestamp() * 1000)
            js_r = int(round((unix_time - z_date_unix_time) / 864e5) // 7)
            js_i = abs(js_r) % 4
            map_idx = qs[js_i]
            relevant_types = COLLECTIONS_MAP[map_idx]
            for col_type in relevant_types:
                entries.append(Collection(d, col_type, ICON_MAP.get(col_type)))

        return entries
