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

        dates = self.get_dates(session)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        
        return entries

    def get_dates(self, session: requests.Session) -> list:
        current_calendar = self.get_calendar_from_site(session)
        calendar = self.clean_ics(current_calendar)
        dates = self._ics.convert(calendar)

        # in december the calendar for the next year is available
        if self.month == 12:
            self.year += 1
            next_calendar = self.get_calendar_from_site(session)
            calendar = self.clean_ics(next_calendar)
            dates += self._ics.convert(calendar)

        return dates

    def get_calendar_from_site(self, session: requests.Session) -> str:
        # example format: https://www.staedteservice.de/abfallkalender_1_477_2023.ics
        URL = BASE_URL+"_"+self.city_code+"_"+self.street_number+"_"+str(self.year)+".ics"

        r = session.get(URL)
        r.raise_for_status()
        r.encoding = "utf-8"  # enshure it is the right encoding

        return r.text
    
    def get_city_code(self) -> str:
        # returns the city_code based on the city input
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
        year = int(date.strftime("%Y"))

        return year

    def get_month(self) -> int:
        # returns the current month

        currentDateTime = datetime.datetime.now()
        date = currentDateTime.date()
        month = int(date.strftime("%m"))

        return month

    def clean_ics(self, calendar: str) -> str:
        # clean ics from problematic lines
        
        # lines to be removed from ics
        remove_tuple = ("BEGIN:VALARM", "TRIGGER", "ACTION:DISPLAY", "DESCRIPTION", "END:VALARM")

        # split lines
        split_calendar = calendar.split("\n")
        clean_calendar = ""

        # do cleanup
        for index in range(0,len(split_calendar)):
            for word in remove_tuple:
                if word in split_calendar[index]:
                    split_calendar[index] = ""
                    break
            if split_calendar[index] != "":
                clean_calendar += split_calendar[index]+"\n"

        return clean_calendar