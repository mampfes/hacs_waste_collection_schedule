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
        ),
        (
            "Esslingen, Bahnhof",
            {
                "url": "https://api.abfall.io/?kh=DaA02103019b46345f1998698563DaAd&t=ics&s=1a862df26f6943997cef90233877a4fe"
            },
        ),
    ]
)


HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(self, url, offset=None):
        self._url = url
        self._offset = offset

    def fetch(self):
        if "{%Y}" in self._url:
            # url contains wildcard
            now = datetime.datetime.now()
            url = self._url.replace("{%Y}", str(now.year))
            entries = self.fetch_year(url)
            if now.month == 12:
                # also get data for next year if we are already in december
                url = self._url.replace("{%Y}", str(now.year + 1))
                try:
                    entries.extend(self.fetch_year(url))
                except Exception:
                    # ignore if fetch for next year fails
                    pass
            return entries
        else:
            return self.fetch_year(self._url)

    def fetch_year(self, url):
        # get ics file
        r = requests.get(url, headers=HEADERS)
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
                if self._offset is not None:
                    dtstart += datetime.timedelta(days=self._offset)
                summary = str(e.get("summary"))
                entries.append(CollectionAppointment(dtstart, summary))

        return entries
