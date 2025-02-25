####Mod by SEMATpl - semat.pl - based on sepan_remondis_pl ###
import datetime
import json
import logging
import defusedxml.ElementTree as XMLDEFUSE

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]


TITLE = "Kleszczewo/Kostrzyn"
DESCRIPTION = "Source for Kleszczewo/Kostrzyn commune garbage collection"
URL = "https://www.puk-zys.pl/index.php/harmonogram-wywozow-2024-r/" #Only Kleszczewo and Kostrzyn
TEST_CASES = {
    "Street Name": {
        "city": "Komorniki",
        "street_name": "Komorniki",
        "street_number": "93/2",
        "commune_name": "Komorniki"
    },
}

_LOGGER = logging.getLogger(__name__)


API_URL = "https://zys-harmonogram.smok.net.pl/{}/{}"
#API_URL = "https://zys-harmonogram.smok.net.pl/kleszczewo/2025" #FOR test_sources.py 

ICON_MAP = {
    1: "mdi:trash-can",
    2: "mdi:recycle",
    3: "mdi:recycle",
    4: "mdi:recycle",
    5: "mdi:recycle",
    6: "mdi:recycle",
    7: "mdi:trash-can",
}


class Source:
    def __init__(self, city, street_name, street_number, commune_name):
        self._city = city.upper()
        self._street_name = street_name.upper()
        self._street_number = street_number.upper()
        self._commune_name = commune_name.lower()


    def fetch(self):
        try:
            return self.get_data(API_URL.format(self._commune_name,datetime.datetime.now().year))
        except Exception:
            _LOGGER.debug(
                f"fetch failed for source {TITLE}: trying different API_URL ..."
            )
            return self.get_data(API_URL.format(""))

    def get_data(self, api_url):
        r = requests.get(f"{api_url}/addresses/cities")
        r.raise_for_status()
        city_id = 0
        cities = json.loads(r.text)
        for item in cities:
            if item["value"] == self._city:
                city_id = item["id"]
        if city_id == 0:
            raise Exception("city not found")

        r = requests.get(f"{api_url}/addresses/streets/{city_id}")
        r.raise_for_status()
        street_id = 0
        streets = json.loads(r.text)
        for item in streets:
            if item["value"] == self._street_name:
                street_id = item["id"]
        if street_id == 0:
            raise Exception("street not found")

        r = requests.get(f"{api_url}/addresses/numbers/{city_id}/{street_id}")
        r.raise_for_status()
        number_id = 0
        numbers = json.loads(r.text)
        for item in numbers:
            if item["value"] == self._street_number:
                number_id = item["id"]
        if number_id == 0:
            raise Exception("number not found")

        r = requests.get(f"{api_url}/reports", params={"type": "html","id": number_id})
        r.raise_for_status()
        report = json.loads(r.text)
        if report["status"] != "success":
            raise Exception("fetch report failed")

        r = requests.get(report["filePath"])
        r.raise_for_status()
        r.encoding = 'utf-8'
        table = r.text[r.text.find("<table") : r.text.rfind("</table>") + 8]
        tree = XMLDEFUSE.fromstring(table)
        year = datetime.date.today().year

        entries = []
        NAME_MAP = [th.text.strip() for th in tree.findall(".//th")][1:]

        for row_index, row in enumerate(tree.findall(".//tr")):
            if row_index == 0 or row_index > 13:
                continue
            for cell_index, cell in enumerate(row.findall(".//td")):
                if (
                    cell_index == 0
                    or not isinstance(cell.text, str)
                    or not cell.text.strip()
                ):
                    continue

                for day in cell.text.split(","):
                    entries.append(
                        Collection(
                            datetime.date(year, row_index - 1, int(day)),
                            NAME_MAP[cell_index],
                            ICON_MAP[cell_index],
                        )
                    )

        return entries
        