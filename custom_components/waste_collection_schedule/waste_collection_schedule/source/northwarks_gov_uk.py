import logging
from io import BytesIO

import pdfplumber
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Warwickshire Borough Council"
DESCRIPTION = (
    "Source for waste collection services for North Warwickshire Borough Council"
)
URL = "https://www.northwarks.gov.uk"
TEST_CASES = {
    "Test_001": {"house_number": 43, "street": "Laburnum Close", "postcode": "B78 2JH"},
    "Test_002": {"house_number": 18, "street": "Morgan Close", "postcode": "CV7 8PR"},
    "Test_003": {"house_number": "76", "street": "Main Road", "postcode": "cv9 3eg"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling & Garden Waste": "mdi:recycle",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
URLS: dict = {
    "SEARCH": "https://www.northwarks.gov.uk/directory/search",
    "CALENDAR": "https://www.northwarks.gov.uk/",
}


class Source:
    def __init__(self, house_number: str | int, street: str, postcode: str):
        self._house_number: str = str(house_number).upper()
        self._street: str = str(street.upper())
        self._postcode: str = str(postcode.upper())
        self._address: str = f"{self._house_number} {self._street}"

    def fetch(self):
        s = requests.Session()

        # Get postcode address list
        params: dict = {
            "directoryID": 3,
            "showInMap": "",
            "keywords": self._postcode,
            "search": "Search directory",
        }
        r = s.get(
            URLS["SEARCH"],
            headers=HEADERS,
            params=params,
        )

        # extract address-specific url
        soup = BeautifulSoup(r.content, "html.parser")
        list_items = soup.find_all("a", {"class": "list__link"})
        for item in list_items:
            if item.text.startswith(self._address):
                href = item.get("href")

        # get page containing calendar url
        r = s.get(
            URLS["CALENDAR"] + href,
            headers=HEADERS,
        )
        soup = BeautifulSoup(r.content, "html.parser")
        calendar_link = soup.find(
            "dd", {"class": "definition__content definition__content--link"}
        ).find("a")
        calendar_url = calendar_link.get("href")

        # get pdf calendar
        calendar_pdf = s.get(
            calendar_url,
            headers=HEADERS,
        )

        # suppress error messages while processing pdf
        logging.getLogger("pdfminer").setLevel(logging.ERROR)

        # load pdf and extract table on first page
        with pdfplumber.open(BytesIO(calendar_pdf.content)) as pdf:
            table = pdf.pages[0].extract_table()

        # first row contains the waste types
        waste_types = [
            f"{item}".replace("\n", " ") if item is not None else item
            for item in table[0][1:]
        ]

        # remaining rows contain calendar month and collection date
        schedule: dict = {}
        for lst in table[1:]:
            temp_row = [
                "_" if item == "" else f"{item} {lst[0].replace('\n', ' ')}"
                for item in lst[1:]
            ]
            for idx, item in enumerate(temp_row):
                if item != "_":
                    dt = item
                    # change problematic abbreviations
                    if dt.startswith("Thurs"):
                        dt = item.replace("Thurs", "Thu").replace("\n", " ")
                    schedule.update({dt: waste_types[idx]})

        # create entries from key:value pairs
        entries = []
        for d, w in schedule.items():
            entries.append(
                Collection(
                    date=parser.parse(d).date(),
                    t=w,
                    icon=ICON_MAP.get(w),
                )
            )

        return entries
