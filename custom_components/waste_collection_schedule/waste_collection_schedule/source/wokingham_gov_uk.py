import re
from datetime import date as date_type
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Wokingham Borough Council"
DESCRIPTION = "Source for wokingham.gov.uk services for Wokingham, UK."
URL = "https://wokingham.gov.uk"
API_URL = "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day"
TEST_CASES = {
    "Test_001": {"postcode": "RG40 1GE", "property": "10032935729"},
    "Test_002": {"postcode": "RG413BP", "property": "14007633"},
    "Test_003": {"postcode": "rg41 1ph", "property": 14040037},
    "Test_004": {"postcode": "RG40 2LW", "address": "16 Davy Close"},
    "No-Collection Test": {"postcode": "RG10 0EU", "address": "39 Broadwater Road"},
}
ICON_MAP = {
    "HOUSEHOLD WASTE": Icons.GENERAL_WASTE,
    "GARDEN WASTE": Icons.GARDEN,
    "RECYCLING": Icons.RECYCLING,
    "FOOD WASTE": Icons.BIO_KITCHEN,
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.wokingham.gov.uk",
    "Origin": "https://www.wokingham.gov.uk",
    "Referer": "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day",
}


class Source:
    def __init__(self, postcode=None, property=None, address=None):
        self._postcode = postcode
        self._property = property
        self._address = address

    def get_form_id(self, txt: str) -> str:
        soup = BeautifulSoup(txt, "html.parser")
        x = soup.find("input", {"name": "form_build_id"})
        id = x.get("value")
        return id

    def match_address(self, lst: list, addr: str) -> str:
        for item in lst:
            if addr in item.text.replace(",", ""):
                a = item.get("value")
        return a

    @staticmethod
    def _parse_day_month(text: str):
        """Parse e.g. 'Thursday 25 December' -> (weekday, day, month) or None."""
        m = re.search(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)", text)
        if not m:
            return None
        try:
            weekday = datetime.strptime(m.group(1)[:3], "%a").weekday()
            month = datetime.strptime(m.group(3)[:3], "%b").month
            day = int(m.group(2))
        except ValueError:
            return None
        return weekday, day, month

    def parse_revised_schedules(self, txt: str) -> dict:
        """Return {(day, month): (weekday, day, month)} of rescheduled dates.

        The council publishes holiday adjustments in a table (normal date ->
        rescheduled date, without a year) above the postcode look-up on the
        main page. Rows such as "No change" are ignored.
        """
        revised: dict = {}
        soup = BeautifulSoup(txt, "html.parser")
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            normal = self._parse_day_month(tds[0].get_text(" ", strip=True))
            new = self._parse_day_month(tds[1].get_text(" ", strip=True))
            if normal is None or new is None:
                continue
            if normal[1:] == new[1:]:
                continue
            revised[normal[1:]] = new
        return revised

    @staticmethod
    def apply_revision(revised: dict, date: date_type) -> date_type:
        new = revised.get((date.day, date.month))
        if new is None:
            return date
        _, day, month = new
        year = date.year + (1 if month < date.month else 0)
        try:
            return date.replace(year=year, month=month, day=day)
        except ValueError:
            return date

    def fetch(self):
        s = requests.Session()

        # Load page to generate token needed for subsequent query. The same page
        # also contains the holiday (e.g. Christmas) schedule adjustments table.
        r = s.get(API_URL)
        form_id = self.get_form_id(r.text)
        revised_schedules = self.parse_revised_schedules(r.text)

        # Perform postcode search to generate token needed for following query
        self._postcode = str(self._postcode.upper().strip().replace(" ", ""))
        payload = {
            "postcode_search": self._postcode,
            "op": "Find Address",
            "form_build_id": form_id,
            "form_id": "waste_collection_api_form",
        }
        r = s.post(
            API_URL,
            headers=HEADERS,
            data=payload,
        )
        form_id = self.get_form_id(r.text)

        # Use address to get an ID if property wasn't supplied. Assumes first match is correct.
        if self._property is None:
            soup = BeautifulSoup(r.text, "html.parser")
            dropdown = soup.find("div", {"class": "form-item__dropdown"})
            addresses = dropdown.find_all("option")
            self._address = self._address.upper()
            self._property = self.match_address(addresses, self._address)
        else:
            self._property = str(self._property)

        # Now get the regular collection schedule
        payload = {
            "postcode_search": self._postcode,
            "address_options": self._property,
            "op": "Show collection dates",
            "form_build_id": form_id,
            "form_id": "waste_collection_api_form",
        }
        r = s.post(
            API_URL,
            headers=HEADERS,
            data=payload,
        )
        soup = BeautifulSoup(r.text, "html.parser")

        # The results page may repeat the adjustments table; merge if present
        for k, v in self.parse_revised_schedules(r.text).items():
            revised_schedules.setdefault(k, v)

        entries = []

        # Extract the collection schedules
        cards = soup.find_all("div", {"class": "card--waste"})
        for card in cards:
            # Cope with waste suffixed with (week 1) or (week 2)
            waste_type = card.find("h3").text.split("(")[0].strip()
            waste_date = card.find("span").text.strip().split()[-1]
            try:
                date = datetime.strptime(waste_date, "%d/%m/%Y").date()
            except ValueError:
                # occurs if next collections date shows as "No collection"
                continue

            # apply Christmas & New Year (or other holiday) adjustments
            date = self.apply_revision(revised_schedules, date)

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.upper()),
                )
            )

        return entries
