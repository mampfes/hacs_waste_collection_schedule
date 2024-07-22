from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "AWISTA LOGISTIK Stadt Remscheid"
DESCRIPTION = "Source for AWISTA LOGISTIK Stadt Remscheid."
URL = "https://www.monaloga.de/"
TEST_CASES = {
    "Adolf-Clarenbach-Straße 42899": {
        "street": "Adolf-Clarenbach-Straße",
        "plz": 42899,
    },
    "Alte Wendung": {"street": "Alte Wendung"},
}


ICON_MAP = {
    "Leichtverpackungen": "mdi:recycle",
}

GERMAN_MONTHS = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


API_URL = "https://www.monaloga.de/mportal/awista-logistik/stadt-remscheid/index.php"


PARAM_TRANSLATIONS = {
    "de": {
        "plz": "PLZ",
        "street": "Straße",
    },
    "en": {
        "plz": "ZIP",
        "street": "Street",
    },
}


class Source:
    def __init__(self, street: str, plz: str | int | None = None):
        self._street: str = street
        self._plz: str | None = str(plz).strip() if plz else None

    def fetch(self):
        args = {
            "form_ident": ["1", "0"],
            "sessionid": "",
            "form_ident_source": "1",
            "year": datetime.now().year,
            "next": "Suchen",
        }

        # get json file
        r = requests.post(API_URL, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", {"name": "a_street"})
        options = select.find_all("option")
        street_id = None

        street_search = self._street.lower().strip()

        for option in options:
            street_name = option.text.split("(")[0].lower().strip()
            if street_name == street_search and (
                not self._plz or self._plz in option.text
            ):
                street_id = option["value"]
                break
        if street_id is None:
            raise ValueError(
                f"Street PLZ combination not found: {self._street} with {self._plz}"
            )

        args["form_ident"] = "1"
        args["a_street"] = street_id + "|" + self._street.strip()

        r = requests.post(API_URL, args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.find("div", {"id": "tab1"})
        data = data.find("table")

        rows = data.find_all("tr")

        entries = []
        for row in rows:
            cols = row.find_all("td")
            bin_type = cols[-1].text.strip()
            date_str = cols[0].text.split(",")[-1].strip()

            date_parts = date_str.split(" ")
            day = int(date_parts[0].strip(".").strip())
            month = GERMAN_MONTHS[date_parts[1].strip()]
            year = int(date_parts[2].strip())
            d = date(year=year, month=month, day=day)
            icon = ICON_MAP.get(bin_type.lower())  # Collection icon
            entries.append(Collection(date=d, t=bin_type, icon=icon))

        return entries
