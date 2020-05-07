import requests
import datetime
import icalendar
from collections import OrderedDict
from pathlib import Path


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
        (
            "Test File",
            {
                # Path is used here to allow to call the Source from any location.
                # This is not required in a yaml configuration!
                "file": Path(__file__)
                .resolve()
                .parents[1]
                .joinpath("test/test.ics")
            },
        ),
    ]
)


HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(self, url=None, file=None, offset=None):
        self._url = url
        self._file = file
        self._offset = offset
        if bool(self._url is not None) == bool(self._file is not None):
            raise RuntimeError("Specify either url or file")

    def fetch(self):
        if self._url is not None:
            if "{%Y}" in self._url:
                # url contains wildcard
                now = datetime.datetime.now()
                url = self._url.replace("{%Y}", str(now.year))
                entries = self.fetch_url(url)
                if now.month == 12:
                    # also get data for next year if we are already in december
                    url = self._url.replace("{%Y}", str(now.year + 1))
                    try:
                        entries.extend(self.fetch_url(url))
                    except Exception:
                        # ignore if fetch for next year fails
                        pass
                return entries
            else:
                return self.fetch_url(self._url)
        elif self._file is not None:
            return self.fetch_file(self._file)

    def fetch_url(self, url):
        # get ics file
        r = requests.get(url, headers=HEADERS)
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly

        return self._convert(r.text)

    def fetch_file(self, file):
        f = open(file, "r")
        return self._convert(f.read())

    def _convert(self, data):
        entries = []

        # parse ics file
        calender = icalendar.Calendar.from_ical(data)

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
