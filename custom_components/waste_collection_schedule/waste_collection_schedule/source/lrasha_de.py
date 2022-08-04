import datetime
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS


TITLE = "Landkreis Schwäbisch Hall"
DESCRIPTION = "Source for lrasha.de - Landkreis Schwäbisch Hall"
URL = "https://exchange.cmcitymedia.de/landkreis-schwaebisch-hallt3/wasteCalendarExport.php"
# https://www.lrasha.de/de/buergerservice/abfallwirtschaft/abfallkalender
TEST_CASES = {
    "Ilshofen": {"location": 114}
}


class Source:
    def __init__(self, location):
        self._location = location
        self._ics = ICS()

    def fetch(self):
        # get ics file
        full_url = "https://exchange.cmcitymedia.de/landkreis-schwaebisch-hallt3/wasteCalendarExport.php" + "?location=" + self._location
        r = requests.get(full_url)
        r.raise_for_status()
        
        # parse ics file
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)
        
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
