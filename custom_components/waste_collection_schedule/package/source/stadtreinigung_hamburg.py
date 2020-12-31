import requests

from ..helpers import CollectionAppointment
from ..service.ICS import ICS

DESCRIPTION = "Source for Stadtreinigung.Hamburg based services."
URL = "https://www.stadtreinigung.hamburg"
TEST_CASES = {
    "Hamburg": {"asId": 5087, "hnId": 113084},
}


class Source:
    def __init__(self, asId, hnId):
        self._asId = asId
        self._hnId = hnId
        self._ics = ICS(offset=1, regex="Erinnerung: Abfuhr (.*) morgen")

    def fetch(self):
        args = {"asId": self._asId, "hnId": self._hnId, "adresse": "MeineAdresse"}

        # get ics file
        r = requests.post(
            f"https://www.stadtreinigung.hamburg/privatkunden/abfuhrkalender/Abfuhrtermin.ics",
            data=args,
        )

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(CollectionAppointment(d[0], d[1]))
        return entries
