import datetime
import logging
import re
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AbfallIO import SERVICE_MAP
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfall.IO / AbfallPlus"
DESCRIPTION = (
    "Source for AbfallPlus.de waste collection. Service is hosted on abfall.io."
)
URL = "https://www.abfallplus.de"
COUNTRY = "de"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": s["url"],
            "default_params": {"key": s["service_id"]},
        }
        for s in SERVICE_MAP
    ]


TEST_CASES = {
    "Landshut": {
        "key": "bd0c2d0177a0849a905cded5cb734a6f",
        "f_id_kommune": 2655,
        "f_id_bezirk": 2655,
        "f_id_strasse": 763,
        # "f_abfallarten": [31, 17, 19, 218]
    },
    "Schoenmackers": {
        "key": "e5543a3e190cb8d91c645660ad60965f",
        "f_id_kommune": 3682,
        "f_id_strasse": "3682adenauerplatz",
        "f_id_strasse_hnr": "20417",
        # "f_abfallarten": [691,692,696,695,694,701,700,693,703,704,697,699],
    },
    "Ludwigshafen am Rhein": {
        "key": "6efba91e69a5b454ac0ae3497978fe1d",
        "f_id_kommune": "5916",
        "f_id_strasse": "5916abteistrasse",
        "f_id_strasse_hnr": 33,
    },
    "AWB Limburg-Weilburg": {
        "key": "0ff491ffdf614d6f34870659c0c8d917",
        "f_id_kommune": 6031,
        "f_id_strasse": 621,
        "f_id_strasse_hnr": 872,
        "f_abfallarten": [27, 28, 17, 67],
    },
}
_LOGGER = logging.getLogger(__name__)

MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
}


# Parser for HTML input (hidden) text
class HiddenInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._args = {}

    @property
    def args(self):
        return self._args

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if d["type"] == "hidden":
                self._args[d["name"]] = d["value"]


class Source:
    def __init__(
        self,
        key,
        f_id_kommune,
        f_id_strasse,
        f_id_bezirk=None,
        f_id_strasse_hnr=None,
        f_abfallarten=[],
    ):
        self._key = key
        self._kommune = f_id_kommune
        self._bezirk = f_id_bezirk
        self._strasse = f_id_strasse
        self._strasse_hnr = f_id_strasse_hnr
        self._abfallarten = f_abfallarten  # list of integers
        self._ics = ICS()

    def fetch(self):
        # get token
        params = {"key": self._key, "modus": MODUS_KEY, "waction": "init"}

        r = requests.post("https://api.abfall.io", params=params, headers=HEADERS)
        if r.status_code == 401:
            raise ValueError(
                f"API key '{self._key}' is no longer valid for the legacy abfall.io API. "
                "This provider may have migrated to the new abfall.io v3 API, which is not yet supported. "
                "See https://github.com/mampfes/hacs_waste_collection_schedule/issues/3788"
            )
        r.raise_for_status()

        # add all hidden input fields to form data
        # There is one hidden field which acts as a token:
        # It consists of a UUID key and a UUID value.
        p = HiddenInputParser()
        p.feed(r.text)
        args = p.args

        args["f_id_kommune"] = self._kommune
        args["f_id_strasse"] = self._strasse

        if self._bezirk is not None:
            args["f_id_bezirk"] = self._bezirk

        if self._strasse_hnr is not None:
            args["f_id_strasse_hnr"] = self._strasse_hnr

        for i in range(len(self._abfallarten)):
            args[f"f_id_abfalltyp_{i}"] = self._abfallarten[i]

        args["f_abfallarten_index_max"] = len(self._abfallarten)
        args["f_abfallarten"] = ",".join(map(lambda x: str(x), self._abfallarten))

        now = datetime.datetime.now()
        date2 = now + datetime.timedelta(days=365)
        args["f_zeitraum"] = f"{now.strftime('%Y%m%d')}-{date2.strftime('%Y%m%d')}"

        params = {"key": self._key, "modus": MODUS_KEY, "waction": "export_ics"}

        # get csv file
        r = requests.post(
            "https://api.abfall.io", params=params, data=args, headers=HEADERS
        )

        # parse ics file
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        ics_file = r.text

        # Remove all lines starting with <b
        # This warning are caused for customers which use an extra radiobutton
        # list to add special waste types:
        # - AWB Limburg-Weilheim uses this list to select a "Sonderabfall <city>"
        #   waste type. The warning could be removed by adding the extra config
        #   option "f_abfallarten" with the following values [27, 28, 17, 67]
        html_warnings = re.findall(r"\<b.*", ics_file)
        if html_warnings:
            ics_file = re.sub(r"\<br.*|\<b.*", "\\r", ics_file)
            # _LOGGER.warning("Html tags removed from ics file: " + ', '.join(html_warnings))

        entries = []
        for ev in self._ics.convert_events(ics_file):
            entries.append(
                Collection(
                    ev.date,
                    ev.title,
                    location=ev.location,
                    description=ev.description,
                )
            )
        return entries
