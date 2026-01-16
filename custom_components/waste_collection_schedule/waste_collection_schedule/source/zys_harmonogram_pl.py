# ### Mod by SEMATpl - semat.pl - based on sepan_remondis_pl ###
import datetime
import json
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Kleszczewo/Kostrzyn"
DESCRIPTION = "Source for Kleszczewo/Kostrzyn commune garbage collection"
URL = "https://www.puk-zys.pl/index.php/harmonogram-wywozow-2024-r/"  # Only Kleszczewo and Kostrzyn
TEST_CASES = {
    "Street Name": {
        "city": "Komorniki",
        "street_name": "Komorniki",
        "street_number": "93/2",
        "commune_name": "Kleszczewo",
    },
}

_LOGGER = logging.getLogger(__name__)


API_URL = "https://zys-harmonogram.smok.net.pl/{}/{}"

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
            return self.get_data(
                API_URL.format(self._commune_name, datetime.datetime.now().year)
            )
        except Exception:
            _LOGGER.debug(
                f"fetch failed for source {TITLE}: trying different API_URL ..."
            )
            return self.get_data(API_URL.format("", ""))

    def get_data(self, api_url):
        r = requests.get(f"{api_url}/addresses/cities")
        r.raise_for_status()
        city_id = 0
        cities = json.loads(r.text)
        for item in cities:
            if item["value"].upper() == self._city:
                city_id = item["id"]
        if city_id == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, [c["value"] for c in cities]
            )

        r = requests.get(f"{api_url}/addresses/streets/{city_id}")
        r.raise_for_status()
        street_id = 0
        streets = json.loads(r.text)
        for item in streets:
            if item["value"].upper() == self._street_name:
                street_id = item["id"]
        if street_id == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name", self._street_name, [s["value"] for s in streets]
            )

        r = requests.get(f"{api_url}/addresses/numbers/{city_id}/{street_id}")
        r.raise_for_status()
        number_id = 0
        numbers = json.loads(r.text)
        for item in numbers:
            if item["value"] == self._street_number:
                number_id = item["id"]
        if number_id == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_number", self._street_number, [n["value"] for n in numbers]
            )

        r = requests.get(f"{api_url}/reports", params={"type": "html", "id": number_id})
        r.raise_for_status()
        report = json.loads(r.text)
        if report["status"] != "success":
            raise Exception("fetch report failed")

        r = requests.get(report["filePath"])
        r.raise_for_status()
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table")
        if not table:
            raise Exception("Table not found in the HTML response")

        year = datetime.date.today().year
        entries = []
        NAME_MAP = [th.text.strip() for th in table.find_all("th")][1:]

        for row_index, row in enumerate(table.find_all("tr")):
            if row_index == 0 or row_index > 13:
                continue
            cells = row.find_all("td")
            for cell_index, cell in enumerate(cells):
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
                            ICON_MAP.get(
                                cell_index, "mdi:trash-can"
                            ),  # Default to trash can if no icon is found
                        )
                    )

        return entries
