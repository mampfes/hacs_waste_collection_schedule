import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS


TITLE = "Stadtreinigung Dresden"
DESCRIPTION = "Source for Stadtreinigung Dresden waste collection."
URL = "https://stadtplan.dresden.de/project/cardo3Apps/IDU_DDStadtplan/abfall/ical.ashx"
TEST_CASES = {
    "Neumarkt 6": {"standort": 80542},
}


class Source:
    def __init__(self, standort, asId=None):
        self._standort = standort
        self._ics = ICS()

    def fetch(self):

        now = datetime.datetime.now().date()
        
        r = requests.get(
            URL,
            params={
                "STANDORT": self._standort,
                "DATUM_VON": now.strftime("%d.%m.%Y"),
                "DATUM_BIS": (now + datetime.timedelta(days=365)).strftime("%d.%m.%Y"),
            },
        )

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
