import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

import urllib
import icalendar


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

    def fetch(self):

        args = {
            'id': 430,
            'tx_citkoabfall_abfallkalender[strasse]': self._street.encode('utf-8'),
            'tx_citkoabfall_abfallkalender[hausnummer]': self._house_number.encode('utf-8'),
            'tx_citkoabfall_abfallkalender[abfallarten][0]': 61,
            'tx_citkoabfall_abfallkalender[abfallarten][1]': 60,
            'tx_citkoabfall_abfallkalender[abfallarten][2]': 59,
            'tx_citkoabfall_abfallkalender[abfallarten][3]': 58,
            'tx_citkoabfall_abfallkalender[action]': 'ics',
            'tx_citkoabfall_abfallkalender[controller]': 'FrontendIcs'
        }

        # use '%20' instead of '+' in URL
        # https://stackoverflow.com/questions/21823965/use-20-instead-of-for-space-in-python-query-parameters
        args = urllib.parse.urlencode(args, quote_via=urllib.parse.quote)

        # post request
        reply = requests.get(URL, params=args)

        # create calender from reply
        gcal = icalendar.Calendar.from_ical(reply.text)

        # iterate over events and add to waste collection
        entries = []
        for component in gcal.walk():
            if component.name == "VEVENT":
                type = component.get('summary')
                start_date = component.get('dtstart').dt

                entries.append(Collection(start_date, type))

        return entries
