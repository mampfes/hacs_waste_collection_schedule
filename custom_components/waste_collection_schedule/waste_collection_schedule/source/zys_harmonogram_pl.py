#### Mod by SEMATpl - semat.pl - based on sepan_remondis_pl ###
import datetime
import json
import logging
from bs4 import BeautifulSoup

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kleszczewo/Kostrzyn"
DESCRIPTION = "Source for Kleszczewo/Kostrzyn commune garbage collection"
URL = "https://www.puk-zys.pl/index.php"  # Only Kleszczewo and Kostrzyn
TEST_CASES = {
    "Street Name": {
        "city": "Komorniki",
        "street_name": "Komorniki",
        "street_number": "93/2",
        "commune_name": "Kleszczewo"
    },
}

_LOGGER = logging.getLogger(__name__)
#API_URL = "https://zys-harmonogram.smok.net.pl/kleszczewo/2026" for test
API_URL = "https://zys-harmonogram.smok.net.pl/{}/{}"

ICON_MAP = {
    1: "mdi:trash-can",      # Zmieszane odpady komunalne
    2: "mdi:recycle",        # Paper
    3: "mdi:recycle",        # Metale i tworzywa sztuczne
    4: "mdi:glass-cup",      # Szkło
    5: "mdi:leaf",           # Bioodpady
}

MONTHS = {
    "styczeń": 1,
    "luty": 2,
    "marzec": 3,
    "kwiecień": 4,
    "maj": 5,
    "czerwiec": 6,
    "lipiec": 7,
    "sierpień": 8,
    "wrzesień": 9,
    "październik": 10,
    "listopad": 11,
    "grudzień": 12,
}


class Source:
    def __init__(self, city, street_name, street_number, commune_name):
        self._city = city.upper()
        self._street_name = street_name.upper()
        self._street_number = street_number.upper()
        self._commune_name = commune_name.lower()

    def fetch(self):
        try:
            return self.get_data(API_URL.format(self._commune_name,  datetime.datetime.now().year))
        except Exception:
            _LOGGER.debug(
                f"fetch failed for source {TITLE}: trying different API_URL ..."
            )
            return self.get_data(API_URL.format("", ""))

    def get_data(self, api_url):
        #GET CITY ID
        r = requests.get(f"{api_url}/addresses/cities")
        r.raise_for_status()
        city_id = 0
        cities = json.loads(r.text)
        for item in cities:
            if item["value"] == self._city:
                city_id = item["id"]
        if city_id == 0:
            raise Exception("city not found")

        #GET STREET ID
        r = requests.get(f"{api_url}/addresses/streets/{city_id}")
        r.raise_for_status()
        street_id = 0
        streets = json.loads(r.text)
        for item in streets:
            if item["value"] == self._street_name:
                street_id = item["id"]
        if street_id == 0:
            raise Exception("street not found")

        #GET HOME ID
        r = requests.get(f"{api_url}/addresses/numbers/{city_id}/{street_id}")
        r.raise_for_status()
        number_id = 0
        numbers = json.loads(r.text)
        for item in numbers:
            if item["value"] == self._street_number:
                number_id = item["id"]
        if number_id == 0:
            raise Exception("number not found")

        #GET REPORTS URL
        r = requests.get(f"{api_url}/reports", params={"type": "html", "id": number_id})
        r.raise_for_status()
        report = json.loads(r.text)
        if report["status"] != "success":
            raise Exception("fetch report failed")

        r = requests.get(report["filePath"])
        r.raise_for_status()
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")

        #TABLE PARSER
        tables = soup.find_all("table")
        table = None
        for t in tables:
            headers = [th.text.strip().lower() for th in t.find_all("th")]
            if "miesiąc" in headers and "zmieszane odpady komunalne" in headers:
                table = t
                break
        if not table:
            raise Exception("Table parser failed")

        tbody = table.find("tbody")
        if not tbody:
            raise Exception("Not found <tbody>")

        entries = []

        thead_rows = table.find("thead").find_all("tr")
        NAME_MAP = [th.text.strip() for th in thead_rows[1].find_all("th")][1:]  # pomijamy 'Miesiąc'

        rows = tbody.find_all("tr")
        for row in rows:
            cells = [c.text.strip() for c in row.find_all("td")]
            if len(cells) < 2:
                continue

            month_text = cells[0].lower()
            parts = month_text.split()
            if len(parts) == 2:
                month_name, year = parts
                try:
                    year = int(year)
                except:
                    year = datetime.date.today().year
            else:
                month_name = parts[0]
                year = datetime.date.today().year

            month = MONTHS.get(month_name)
            if not month:
                continue

            for col_index, cell in enumerate(cells[1:], start=1):
                if not cell:
                    continue
                for day in cell.replace(" ", "").split(","):
                    if not day.isdigit():
                        continue
                    entries.append(
                        Collection(
                            datetime.date(year, month, int(day)),
                            NAME_MAP[col_index - 1],
                            ICON_MAP.get(col_index, "mdi:trash-can"),
                        )
                    )

        return entries
