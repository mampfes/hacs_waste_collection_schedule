import requests
from datetime import date, datetime
import icalendar
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Source for Abfallwirtschaft Zollernalbkreis based services"
URL = "https://www.abfallkalender-zak.de"
TEST_CASES = OrderedDict(
    [
        (
            "Ebingen",
            {
                "city": "2,3,4",
                "street": "3",
                "types": ["restmuell",
                            "gelbersack",
                            "papiertonne",
                            "biomuell",
                            "gruenabfall",
                            "schadstoffsammlung",
                            "altpapiersammlung",
                            "schrottsammlung",
                            "weihnachtsbaeume",
                            "elektrosammlung"
                            ]
            },
        ),
        (
            "Erlaheim",
            {
                "city": "79",
                "street": "",
                "types": ["restmuell",
                            "gelbersack",
                            "papiertonne",
                            "biomuell",
                            "gruenabfall",
                            "schadstoffsammlung",
                            "altpapiersammlung",
                            "schrottsammlung",
                            "weihnachtsbaeume",
                            "elektrosammlung"
                            ]
            },
        )
    ]
)


class Source:
    def __init__(self, city, types, street=None):
        self._city = city
        self._street = street
        self._types = types

    def fetch(self):
        now = datetime.now()
        entries = self.fetch_year(now.year, self._city, self._street, self._types)
        if now.month == 12:
            # also get data for next year if we are already in december
            try:
                entries.extend(
                    self.fetch_year((now.year + 1), self._city, self._street, self._types)
                )
            except Exception:
                # ignore if fetch for next year fails
                pass
        return entries

    def fetch_year(self, year, city, street, types):
        args = {
            "city": city,
            "street": street,
            "year": year,
            "types[]": types,
            "go_ics": "Download",
        }

        # get ics file
        r = requests.get(
            f"https://www.abfallkalender-zak.de",
            params=args,
        )

        entries = []

        # parse ics file
        calender = icalendar.Calendar.from_ical(r.text)

        entries = []
        for e in calender.walk():
            if e.name == "VEVENT":
                dtstart = e.get("dtstart").dt
                summary = str(e.get("summary"))
                entries.append(CollectionAppointment(dtstart, summary))

        return entries
