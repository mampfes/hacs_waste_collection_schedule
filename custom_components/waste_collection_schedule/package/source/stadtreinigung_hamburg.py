import re
import requests
import datetime
import icalendar
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Source for Stadtreinigung.Hamburg based services."
URL = "https://www.stadtreinigung.hamburg"
TEST_CASES = OrderedDict([("Hamburg", {"asId": 5087, "hnId": 113084})])


class Source:
    def __init__(self, asId, hnId):
        self._asId = asId
        self._hnId = hnId

    def fetch(self):
        args = {"asId": self._asId, "hnId": self._hnId, "adresse": "MeineAdresse"}

        # get ics file
        r = requests.post(
            f"https://www.stadtreinigung.hamburg/privatkunden/abfuhrkalender/Abfuhrtermin.ics",
            data=args,
        )

        # parse ics file
        calender = icalendar.Calendar.from_ical(r.text)

        # Summary text contains a lot of blabla. This reg-ex tries to extract the waste type.
        regex = re.compile("Erinnerung: Abfuhr (.*) morgen")

        entries = []
        for e in calender.walk():
            if e.name == "VEVENT":
                summary = str(e.get("summary"))
                match = regex.match(summary)
                if match:
                    summary = match.group(1)
                dtstart = e.get("dtstart").dt.date() + datetime.timedelta(
                    days=1
                )  # events are reported 1 day before
                summary = summary
                entries.append(CollectionAppointment(dtstart, summary))

        return entries
