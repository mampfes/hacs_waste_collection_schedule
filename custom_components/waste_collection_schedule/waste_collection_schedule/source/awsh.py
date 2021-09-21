import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWSH"
DESCRIPTION = "Source for Abfallwirtschaft Südstormarn"
URL = "https://www.awsh.de"
TEST_CASES = {
    "Reinbek": {"ortId": 560, "strId": 860, "waste_types": "R02-B02-D02-P04"},
}

class Source:
    def __init__(self, ortId, strId, waste_types=[]):
        self.ortId = ortId
        self.strId = strId
        self.waste_types = waste_types
        self.ics = ICS()

    def fetch(self):

        _waste_types =  "-".join(map(lambda x: str(x), self.waste_types))
        # get ics file
        r = requests.get(f"https://www.awsh.de/api_v2/collection_dates/1/ort/{self.ortId}/strasse/{self.strId}/hausnummern/0/abfallarten/{_waste_types}/kalender.ics")
        return self.convert(r.text)

    def convert(self, data):
            dates = self.ics.convert(data)

            entries = []
            for d in dates:
                entries.append(Collection(d[0], d[1]))
            return entries