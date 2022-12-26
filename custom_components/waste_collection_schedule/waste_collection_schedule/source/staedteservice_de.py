import requests
import datetime

from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Städteservice"
DESCRIPTION = "Städteservice Raunheim Rüsselsheim"
URL = "https://www.staedteservice.de"

TEST_CASES = {
    "Rüsselsheim": {
        "city": "Rüsselsheim",
        "street_number": "411"
    },
    "Raunheim": {
        "city": "Raunheim",
        "street_number": "565"
    },
}

BASE_URL = "https://www.staedteservice.de/abfallkalender"

CITY_CODE_MAP = {  
"Rüsselsheim": 1,
"Raunheim": 2
}

class Source:
    def __init__(self, city, street_number):
        self.city = str(city)
        self.city_code = CITY_CODE_MAP[city]
        self.street_number = str(street_number)
        self._ics = ICS()

    def fetch(self) -> list:
        currentDateTime = datetime.datetime.now()
        year = currentDateTime.year
        month = currentDateTime.month

        session = requests.Session()

        dates = self.get_dates(session, year, month)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        
        return entries

    def get_dates(self, session: requests.Session, year: int, month: int) -> list:
        current_calendar = self.get_calendar_from_site(session, year)
        calendar = self.fix_trigger(current_calendar)
        dates = self._ics.convert(calendar)

        # in december the calendar for the next year is available
        if month == 12:
            year += 1
            next_calendar = self.get_calendar_from_site(session, year)
            calendar = self.fix_trigger(next_calendar)
            dates += self._ics.convert(calendar)

        return dates

    def get_calendar_from_site(self, session: requests.Session, year: int) -> str:
        # example format: https://www.staedteservice.de/abfallkalender_1_477_2023.ics
        URL = f"{BASE_URL}_{self.city_code}_{self.street_number}_{str(year)}.ics"

        r = session.get(URL)
        r.raise_for_status()
        r.encoding = "utf-8"  # enshure it is the right encoding

        return r.text

    def fix_trigger(self, calendar: str) -> str:
        # the "TRIGGER" is set to "-PT1D" in the ical file
        # the integration failes with following log output: ValueError: Invalid iCalendar duration: -PT1D
        # according to this site https://www.kanzaki.com/docs/ical/duration-t.html
        # the "T" should come after the dur-day if there is a dur-time specified and never before dur-day
        # because there is no dur-time specified we can just ignore the "T" in the TRIGGER

        fixed_calendar = calendar.replace("-PT1D", "-P1D")

        return fixed_calendar