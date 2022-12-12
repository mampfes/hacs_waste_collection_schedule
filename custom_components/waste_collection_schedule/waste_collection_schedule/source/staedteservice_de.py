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
        self.street_number = str(street_number)
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        # get parameters for url generation
        city_code = self.get_city_code()
        year = self.get_year()

        # example format: https://www.staedteservice.de/abfallkalender_1_477_2023.ics
        URL = BASE_URL+"_"+city_code+"_"+self.street_number+"_"+year+".ics"

        r = session.post(URL)
        r.raise_for_status()
        r.encoding = "utf-8"  # enshure it is the right encoding

        # cleanup ics
        text = self.clean_ics(r.text)

        # parse ics file
        dates = self._ics.convert(text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
    
    def get_city_code(self) -> str:
        # returns the citycode based on the city input

        city_code = ""
        if self.city == "Rüsselsheim":
            city_code = "1"
        elif self.city == "Raunheim":
            city_code = "2"

        return city_code

    def get_year(self) -> str:
        # returns the current year

        currentDateTime = datetime.datetime.now()
        date = currentDateTime.date()
        
        return date.strftime("%Y")

    def clean_ics(self, text: str) -> str:
        # clean ics from unnecessary lines

        # split text and remove unnecessary lines
        split_text = text.split("\n")
        clean_text = ""

        # unnecessary lines to be removed from ics
        remove_tuple = ("DESCRIPTION", "CATEGORIES", "LOCATION", "URL", "BEGIN:VALARM", "TRIGGER", "ACTION:DISPLAY", "END:VALARM" )

        # do cleanup
        for index in range(0,len(split_text)):
            for word in remove_tuple:
                if word in split_text[index]:
                    split_text[index] = ""
                    break
            if split_text[index] != "":
                clean_text += split_text[index]+"\n"

        return clean_text