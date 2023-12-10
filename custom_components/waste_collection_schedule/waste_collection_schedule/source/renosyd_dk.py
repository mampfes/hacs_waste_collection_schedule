import requests, re, time, datetime
from bs4 import BeautifulSoup, NavigableString
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from typing import List

TITLE = "Renosyd"
DESCRIPTION = "Renosyd collections for Skanderborg and Odder kommunes"
URL = "https://renosyd.dk"
TEST_CASES = {
    "TestCase1": {
        "kommune": "skanderborg",
        "husnummer": 123000,
    },
    "TestCase2": {
        "kommune": "skanderborg",
        "husnummer": 186305,
    },
    "TestCase3": {
        "kommune": "odder",
        "husnummer": 89042,
    },
}

ICON_MAP = {
    "RESTAFFALD": "mdi:trash-can",
    "PAPIR/PAP": "mdi:note-multiple",
    "EMBALLAGE": "mdi:recycle",
    "STORSKRALD": "mdi:dump-truck",
    "HAVEAFFALD": "mdi:leaf",  # Uncertain about this name, can't find an example
}

DANISH_MONTHS = [
    None,
    "jan",
    "feb",
    "mar",
    "apr",
    "maj",
    "jun",
    "jul",
    "aug",
    "sep",
    "okt",
    "nov",
    "dec",
]


class Source:
    def __init__(self, kommune: str, husnummer: int):
        self._kommune = kommune
        self._husnummer = husnummer
        self._api_url = (
            "https://"
            + self._kommune.lower()
            + ".netdialog.renosyd.dk/citizen/default.aspx"
        )

    def fetch(self) -> List[Collection]:
        session = requests.Session()

        session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        address_select = session.get(
            self._api_url,
            cookies={"StoredAddress": str(self._husnummer)},
        )
        address_select.raise_for_status()

        address_select_soup = BeautifulSoup(address_select.text, "html.parser")
        data = {
            i["name"]: i.get("value", "")
            for i in address_select_soup.select("input[name]")
        }

        binfo = session.post(self._api_url, data=data)
        binfo.raise_for_status()

        binfo_soup = BeautifulSoup(binfo.text, "html.parser")

        calendar = binfo_soup.find_all(attrs={"class": "tableContainersAtProperty"})

        months = []
        this_year = time.localtime().tm_year

        for month in calendar[1].find_all("th"):
            value = month.contents[0].strip()
            if value == "Beholder":
                continue

            months.append(datetime.date(this_year, DANISH_MONTHS.index(value), 1))

            if value == "dec":
                this_year += 1

        entries = []

        rows = calendar[1].find_all("tr")

        for row in rows[1:]:
            elements = row.find_all("td")

            result = re.search(
                r"^(\d{1,2}\s?x\s?)([A-Za-z\/]*)(\s*\d{1,4}\s?L)?$",
                elements[0].contents[0].strip(),
            )
            if result is None:
                continue

            container_type = result.groups()[1]

            for idx, element in enumerate(elements[1:]):
                for subelement in element.contents:
                    if not isinstance(subelement, NavigableString):
                        continue

                    if subelement.strip() == "":
                        continue

                    entries.append(
                        Collection(
                            date=months[idx]
                            + datetime.timedelta(days=int(subelement.strip()) - 1),
                            t=container_type,
                            icon=ICON_MAP.get(container_type.upper()),
                        )
                    )
        return entries
