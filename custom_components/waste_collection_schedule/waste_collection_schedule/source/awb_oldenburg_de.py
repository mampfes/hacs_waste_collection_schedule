import urllib

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWB Oldenburg"
DESCRIPTION = "Source for 'Abfallwirtschaftsbetrieb Stadt Oldenburg (Oldb)'."
URL = "https://services.oldenburg.de/index.php"
TEST_CASES = {
    "Polizeiinspektion Oldenburg": {"street": "Friedhofsweg", "house_number": 30}
}


class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = house_number
        self._ics = ICS(regex=r"(.*)\:\s*\!")

    def fetch(self):

        args = {
            "id": 430,
            "tx_citkoabfall_abfallkalender[strasse]": str(self._street).encode("utf-8"),
            "tx_citkoabfall_abfallkalender[hausnummer]": str(self._house_number).encode(
                "utf-8"
            ),
            "tx_citkoabfall_abfallkalender[abfallarten][0]": 61,
            "tx_citkoabfall_abfallkalender[abfallarten][1]": 60,
            "tx_citkoabfall_abfallkalender[abfallarten][2]": 59,
            "tx_citkoabfall_abfallkalender[abfallarten][3]": 58,
            "tx_citkoabfall_abfallkalender[action]": "ics",
            "tx_citkoabfall_abfallkalender[controller]": "FrontendIcs",
        }

        # use '%20' instead of '+' in URL
        # https://stackoverflow.com/questions/21823965/use-20-instead-of-for-space-in-python-query-parameters
        args = urllib.parse.urlencode(args, quote_via=urllib.parse.quote)

        # post request
        r = requests.get(URL, params=args)

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
