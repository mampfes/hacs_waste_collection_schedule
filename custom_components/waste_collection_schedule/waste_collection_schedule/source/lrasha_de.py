import datetime
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS


TITLE = "Landkreis Schwäbisch Hall"
DESCRIPTION = "Source for lrasha.de - Landkreis Schwäbisch Hall"
URL = "https://exchange.cmcitymedia.de/landkreis-schwaebisch-hallt3/wasteCalendarExport.php"
TEST_CASES = { # Insert arguments for test cases using test_sources.py script
    "TestName": {"arg1": 100, "arg2": "street"}
}


class Source:
    def __init__(self, location):
        self._location = location
        self._ics = ICS()

    def fetch(self):
        # get ics file
        full_url = {URL} + "?location=" + self._location
        r = requests.get(full_url)
        
        # parse ics file
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)
        
        entries = []

#        entries.append(
#            Collection(
#                datetime.datetime(2020, 4, 11),
#                "Waste Type",
#            )
#        )

        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
