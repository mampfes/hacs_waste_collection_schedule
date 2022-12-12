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

ICS_HEAD = """BEGIN:VCALENDAR
METHOD:PUBLISH
PRODID:-//www.staedteservice.de//Abfallkalender//EN
VERSION:2.0
X-WR-CALNAME:Abfallkalender
X-WR-CALDESC:Abfallkalender
X-WR-TIMEZONE:Europe/Berlin
"""

ICS_BOTTOM = "END:VCALENDAR"

class Source:
    def __init__(self, city, street_number):
        self.city = str(city)
        self.city_code = self.get_city_code()
        self.street_number = str(street_number)
        self.year = self.get_year()
        self.month = self.get_month()
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        calendar = self.build_calendar(session)

        # parse ics file
        dates = self._ics.convert(calendar)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries

    def build_calendar(self, session: requests.Session) -> str:
        calendar = ""
        calendar += ICS_HEAD

        current_calendar = self.get_calendar_from_site(session)

        # cleanup ics
        calendar += self.clean_ics(current_calendar)

        # in December the calendar for the next year is available
        if self.month > 11:
            self.year += 1
            next_calendar = self.get_calendar_from_site(session)

            # cleanup ics
            calendar += self.clean_ics(next_calendar)

        calendar += ICS_BOTTOM

        return calendar

    def get_calendar_from_site(self, session: requests.Session):
        # example format: https://www.staedteservice.de/abfallkalender_1_477_2023.ics
        URL = BASE_URL+"_"+self.city_code+"_"+self.street_number+"_"+str(self.year)+".ics"

        r = session.get(URL)
        r.raise_for_status()
        r.encoding = "utf-8"  # enshure it is the right encoding

        return r.text
    
    def get_city_code(self) -> str:
        # returns the citycode based on the city input

        city_code = ""
        if self.city == "Rüsselsheim":
            city_code = "1"
        elif self.city == "Raunheim":
            city_code = "2"

        return city_code

    def get_year(self) -> int:
        # returns the current year

        currentDateTime = datetime.datetime.now()
        date = currentDateTime.date()
        
        return int(date.strftime("%Y"))

    def get_month(self) -> int:
        # returns the current month

        currentDateTime = datetime.datetime.now()
        date = currentDateTime.date()
        
        return int(date.strftime("%m"))

    def clean_ics(self, calendar: str) -> str:
        # clean ics from unnecessary lines

        # split calendar and remove unnecessary lines
        split_calendar = calendar.split("\n")
        clean_calendar = ""

        # lines to be removed from ics
        remove_tuple = ("DESCRIPTION", "CATEGORIES", "LOCATION", "URL", "BEGIN:VALARM", "TRIGGER", "ACTION:DISPLAY", "END:VALARM", "BEGIN:VCALENDAR", "METHOD:", "PRODID:", "VERSION:", "X-WR-CALNAME:", "X-WR-CALDESC:", "X-WR-TIMEZONE:", "END:VCALENDAR" )

        # do cleanup
        for index in range(0,len(split_calendar)):
            for word in remove_tuple:
                if word in split_calendar[index]:
                    split_calendar[index] = ""
                    break
            if split_calendar[index] != "":
                clean_calendar += split_calendar[index]+"\n"

        return clean_calendar