import requests
import datetime
import icalendar
from collections import OrderedDict

from ..helpers import CollectionAppointment


DESCRIPTION = "Source for ICS based services"
URL = ""
TEST_CASES = OrderedDict(
    [
        (
            "Ludwigsburg",
            {
                "url": "https://www.avl-ludwigsburg.de/fileadmin/Files/Abfallkalender/ICS/Privat/Privat_{%Y}_Ossweil.ics"
            },
        )
    ]
)


class Source:
    def __init__(self, url):
        self.url = url

    def fetch(self):
        if "{%Y}" in self.url:
            # url contains wildcard
            now = datetime.datetime.now()
            url = self.url.replace("{%Y}", str(now.year))
            entries = self.fetch_year(url)
            if now.month == 12:
                # also get data for next year if we are already in december
                url = self.url.replace("{%Y}", str(now.year + 1))
                entries.extend(self.fetch_year(url))
            return entries
        else:
            return self.fetch_year(self.url)

    def fetch_year(self, url):
        # get ics file
        r = requests.get(url)
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly

        entries = []

        # parse ics file
        calender = icalendar.Calendar.from_ical(r.text)

        entries = []
        for e in calender.walk():
            if e.name == "VEVENT":
                dtstart = None
                if type(e.get("dtstart").dt) == datetime.date:
                    dtstart = e.get("dtstart").dt
                elif type(e.get("dtstart").dt) == datetime.datetime:
                    dtstart = e.get("dtstart").dt.date()
                summary = str(e.get("summary"))
                entries.append(CollectionAppointment(dtstart, summary))

        return entries
