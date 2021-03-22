import datetime
from pathlib import Path

import requests

from ..helpers import CollectionAppointment
from ..service.ICS import ICS

TITLE = "ICS"
DESCRIPTION = "Source for ICS based schedules."
URL = ""
TEST_CASES = {
    "Dortmund, Dudenstr. 5": {
        "url": "https://www.edg.de/ical/kalender.ics?Strasse=Dudenstr.&Hausnummer=5&Erinnerung=-1&Abfallart=1,2,3,4"
    },
    "Leipzig, Sandgrubenweg 27": {
        "url": "https://www.stadtreinigung-leipzig.de/leistungen/abfallentsorgung/abfallkalender-entsorgungstermine.html&ical=true&loc=Sandgrubenweg%20%2027&lid=x38296"
    },
    "Ludwigsburg": {
        "url": "https://www.avl-ludwigsburg.de/fileadmin/Files/Abfallkalender/ICS/Privat/Privat_{%Y}_Ossweil.ics"
    },
    "Esslingen, Bahnhof": {
        "url": "https://api.abfall.io/?kh=DaA02103019b46345f1998698563DaAd&t=ics&s=1a862df26f6943997cef90233877a4fe"
    },
    "Test File": {
        # Path is used here to allow to call the Source from any location.
        # This is not required in a yaml configuration!
        "file": Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("test/test.ics")
    },
    "Test File (recurring)": {
        # Path is used here to allow to call the Source from any location.
        # This is not required in a yaml configuration!
        "file": Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("test/recurring.ics")
    },
    "München, Bahnstr. 11": {
        "url": "https://www.awm-muenchen.de/index/abfuhrkalender.html?tx_awmabfuhrkalender_pi1%5Bsection%5D=ics&tx_awmabfuhrkalender_pi1%5Bstandplatzwahl%5D=true&tx_awmabfuhrkalender_pi1%5Bsinglestandplatz%5D=false&tx_awmabfuhrkalender_pi1%5Bstrasse%5D=Bahnstr.&tx_awmabfuhrkalender_pi1%5Bhausnummer%5D=11&tx_awmabfuhrkalender_pi1%5Bstellplatz%5D%5Brestmuell%5D=70024507&tx_awmabfuhrkalender_pi1%5Bstellplatz%5D%5Bpapier%5D=70024507&tx_awmabfuhrkalender_pi1%5Bstellplatz%5D%5Bbio%5D=70024507&tx_awmabfuhrkalender_pi1%5Bleerungszyklus%5D%5BR%5D=001%3BU&tx_awmabfuhrkalender_pi1%5Bleerungszyklus%5D%5BP%5D=1%2F2%3BG&tx_awmabfuhrkalender_pi1%5Bleerungszyklus%5D%5BB%5D=1%2F2%3BU&tx_awmabfuhrkalender_pi1%5Byear%5D={%Y}"
    },
    "Buxtehude, Am Berg": {
        "url": "https://abfall.landkreis-stade.de/api_v2/collection_dates/1/ort/10/strasse/90/hausnummern/1/abfallarten/R02-R04-B02-D04-D12-P04-R12-R14-W0-R22-R24-R31/kalender.ics"
    },
    "Abfall Zollernalbkreis, Ebingen": {
        "url": "https://www.abfallkalender-zak.de",
        "params": {
            "city": "2,3,4",
            "street": "3",
            "types[]": [
                "restmuell",
                "gelbersack",
                "papiertonne",
                "biomuell",
                "gruenabfall",
                "schadstoffsammlung",
                "altpapiersammlung",
                "schrottsammlung",
                "weihnachtsbaeume",
                "elektrosammlung",
            ],
            "go_ics": "Download",
        },
        "year_field": "year",
    },
}


HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(self, url=None, file=None, offset=None, params=None, year_field=None):
        self._url = url
        self._file = file
        if bool(self._url is not None) == bool(self._file is not None):
            raise RuntimeError("Specify either url or file")
        self._ics = ICS(offset)
        self._params = params
        self._year_field = year_field  # replace this field in params with current year

    def fetch(self):
        if self._url is not None:
            if "{%Y}" in self._url or self._year_field is not None:
                # url contains wildcard or params contains year field
                now = datetime.datetime.now()

                # replace year in url
                url = self._url.replace("{%Y}", str(now.year))

                # replace year in params
                if self._year_field is not None:
                    if self._params is None:
                        raise RuntimeError("year_field specified without params")
                    self._params[self._year_field] = str(now.year)

                entries = self.fetch_url(url, self._params)

                if now.month == 12:
                    # also get data for next year if we are already in december
                    url = self._url.replace("{%Y}", str(now.year + 1))
                    self._params[self._year_field] = str(now.year + 1)

                    try:
                        entries.extend(self.fetch_url(url), self._params)
                    except Exception:
                        # ignore if fetch for next year fails
                        pass
                return entries
            else:
                return self.fetch_url(self._url, self._params)
        elif self._file is not None:
            return self.fetch_file(self._file)

    def fetch_url(self, url, params=None):
        # get ics file
        r = requests.get(url, params=params, headers=HEADERS)
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly

        return self._convert(r.text)

    def fetch_file(self, file):
        f = open(file)
        return self._convert(f.read())

    def _convert(self, data):
        dates = self._ics.convert(data)

        entries = []
        for d in dates:
            entries.append(CollectionAppointment(d[0], d[1]))
        return entries
