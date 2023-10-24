import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Tameside Metropolitan Borough Council"
DESCRIPTION = "Source for tameside.gov.uk, Tameside Metropolitan Borough Council, UK"
URL = "https://www.tameside.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "M34 6AG", "uprn": "100011601683"},
    "Test_002": {"postcode": "ol5 9jl", "uprn": "100011548952"},
    "Test_003": {"postcode": "SK148JP", "uprn": 100011573345},
}
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "origin": "https://public.tameside.gov.uk",
    "referrer": "https://public.tameside.gov.uk/forms/bin-dates.asp",
}
API_URL = "https://public.tameside.gov.uk/forms/bin-dates.asp"
ICON_MAP = {
    "GREEN BIN": "mdi:trash-can",
    "BROWN BIN": "mdi:leaf",
    "BLUE BIN": "mdi:newspaper",
    "BLACK BIN": "mdi:glass-fragile",
}
REGEX = r"(st|nd|rd|th)"


class Source:
    def __init__(self, postcode=None, uprn=None):
        self._postcode = postcode.upper().strip().replace(" ", "")
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()
        # Get session cookies
        r = s.get(API_URL, headers=HEADERS)

        # Get collection schedule
        address = self._uprn + "-" + self._postcode
        payload = {
            "F03_I01_SelectAddress": address,
            "AdvanceSearch": "Continue",
            "F01_I02_Postcode": self._postcode,
            "F01_I03_Street": "",
            "F01_I04_Town": "",
            "history": ",1,3,",
        }
        r = s.post(API_URL, headers=HEADERS, data=payload)
        soup = BeautifulSoup(r.text, "html.parser")

        # Reconstruct dates and extract bins
        entries = []
        years = soup.find_all("fieldset", {"class": "year"})
        for year in years:
            y = year.find("h3").text

            months = year.find_all("tr", {"class": "month"})
            for month in months:
                m = month.find("td", {"class": "month"}).text
                m = m

                days = month.find_all("td", {"class": "day"})
                for day in days:
                    d = re.sub(REGEX, "", day.text)
                    dt = d + m + y
                    dt = datetime.strptime(dt, "%d%B%Y").date()

                    bins = day.find_all("img", alt=True)
                    for bin in bins:
                        b = bin.get("alt").replace("_Icon", "").replace("_", " ")
                        entries.append(
                            Collection(
                                date=dt,
                                t=b,
                                icon=ICON_MAP.get(b.upper()),
                            )
                        )

        return entries
