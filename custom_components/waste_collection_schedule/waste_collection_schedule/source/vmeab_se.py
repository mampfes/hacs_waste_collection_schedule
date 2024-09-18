from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Västervik Miljö & Energi"
DESCRIPTION = "Source for Västervik Miljö & Energi."
URL = "https://www.vmeab.se/"
TEST_CASES = {
    "Odensvi Ringsfall 1": {"city": "Odensvi", "street": "Ringsfall 1"},
    "Västervik Örtomtaslingan 1": {"city": "Västervik", "street": "Örtomtaslingan 1"},
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL = "https://www.vmeab.se/api/WasteDisposal/GetAllPickups"

SWEEDISH_MONTHS = {
    "januari": "january",
    "februari": "february",
    "mars": "march",
    "april": "april",
    "maj": "may",
    "juni": "june",
    "juli": "july",
    "augusti": "august",
    "september": "september",
    "oktober": "october",
    "november": "november",
    "december": "december",
}

SWEEDISH_WEEKDAYS = {
    "måndag": "monday",
    "tisdag": "tuesday",
    "onsdag": "wednesday",
    "torsdag": "thursday",
    "fredag": "friday",
    "lördag": "saturday",
    "söndag": "sunday",
}


class Source:
    def __init__(self, city: str, street: str):
        self._city: str = city
        self._street: str = street

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        r = s.get("https://www.vmeab.se/tjanster/avfall--atervinning/min-sophamtning/")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
        if not isinstance(token_tag, Tag):
            raise Exception("Could not find request token in initial page")
        token = token_tag["value"]

        data = {
            "__RequestVerificationToken": token,
            "StreetAddress": self._street,
            "City": self._city,
        }

        r = s.post(API_URL, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        waste_results = soup.select("div.waste-disposal-search-result-item")

        entries = []
        for waste_result in waste_results:
            for waste_type_tag in waste_result.select("h4"):
                waste_type = waste_type_tag.text
                date_string_tag = waste_type_tag.find_next_sibling("p")
                if not date_string_tag:
                    continue
                date_string = date_string_tag.text.lower()
                date_string = date_string.split(": ")[-1]

                # Replace sweedish month/weekday names with english ones
                for sweedish_month, english_month in {
                    **SWEEDISH_MONTHS,
                    **SWEEDISH_WEEKDAYS,
                }.items():
                    date_string = date_string.replace(
                        sweedish_month, str(english_month)
                    )

                # parse date if date does not contain year assume this year if then date is in the past assume next year
                date_ = parse(
                    date_string, dayfirst=True, default=datetime(3004, 1, 1)
                ).date()
                if date_.year == 3004:
                    now = datetime.now()
                    year = now.year
                    if date_.month < now.month:
                        year += 1
                    date_ = date_.replace(year=year)

                icon = ICON_MAP.get(waste_type)
                entries.append(Collection(date=date_, t=waste_type, icon=icon))

        return entries
