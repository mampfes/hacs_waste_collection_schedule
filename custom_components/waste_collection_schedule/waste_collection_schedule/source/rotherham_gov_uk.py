import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from datetime import datetime
from bs4 import BeautifulSoup

TITLE = "Rotherham Metropolitan Borough Council"
DESCRIPTION = "Source for Rotherham Metropolitan Borough Council."
URL = "www.rotherham.gov.uk"
TEST_CASES = {
    "374 Kimberworth Park Rd": {"uprn": 100050846673},
    "76 Dovedale Road": {"uprn": 100050831650},
    "12 Bosville St, Rotherham": {"uprn": "100050818634"},
    "40 Spring St, Rotherham": {"uprn": "100050869740"},
}


ICON_MAP:dict[str, str] = {
    "Pink lid bin": "mdi:trash-can",
    "Brown bin": "mdi:leaf",
    "Green bin": "mdi:package-variant",
    "Black bin": "mdi:recycle",
}


API_URL = "https://www.rotherham.gov.uk/homepage/333/bin-coll"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        args = {
            "address": self._uprn
        }

        # get json file
        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")        
        rows = soup.find("div", class_="widget-bin-collection").find("table").find("tbody").find_all("tr")

        entries = []
        for row in rows:
            columns = row.find_all("td")
            bin_type = columns[0].text.strip()
            date_str = columns[1].text.strip()

            date = datetime.strptime(date_str, "%A, %d %B %Y").date()
            icon = ICON_MAP.get(bin_type) # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
