import requests
import datetime
import icalendar
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Source for AbfallNavi (= regioit.de) based services"
URL = "https://www.regioit.de"
TEST_CASES = OrderedDict(
    [
        (
            "Aachen",
            {
                "kalender": "aachen",
                "ort": "Aachen",
                "strasse": 579002,
                "hnr": 5792003,
                "fraktion": [0, 1, 4, 11],
            },
        ),
        (
            "Lindlar",
            {
                "kalender": "lin",
                "ort": "Lindlar",
                "hnr": None,
                "strasse": 53585,
                "fraktion": [0, 2, 3, 4, 5, 6, 7, 8],
            },
        ),
    ]
)


class Source:
    def __init__(self, kalender, ort, strasse, hnr, fraktion):
        self._kalender = kalender
        self._ort = ort
        self._strasse = strasse
        self._hnr = hnr
        self._fraktion = fraktion  # list of integers

    def fetch(self):
        now = datetime.datetime.now()
        entries = self.fetch_year(now.year)
        if now.month == 12:
            # also get data for next year if we are already in december
            entries.extend(self.fetch_year(now.year + 1))
        return entries

    def fetch_year(self, year):
        args = {
            "format": "ics",
            "jahr": year,
            "ort": self._ort,
            "strasse": self._strasse,
            "fraktion": self._fraktion,
        }

        if self._hnr is not None:
            args["hnr"] = self._hnr

        # get ics file
        r = requests.get(
            f"http://abfallkalender.regioit.de/kalender-{self._kalender}/downloadfile.jsp",
            params=args,
        )

        entries = []

        # parse ics file
        calender = icalendar.Calendar.from_ical(r.text)

        entries = []
        for e in calender.walk():
            if e.name == "VEVENT":
                dtstart = e.get("dtstart").dt.date()
                summary = str(e.get("summary"))
                entries.append(CollectionAppointment(dtstart, summary))

        return entries
