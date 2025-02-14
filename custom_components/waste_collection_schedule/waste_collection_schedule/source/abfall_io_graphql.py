import datetime
import logging
import re
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AbfallIO import SERVICE_MAP
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfall.IO GraphQL"
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
    "Neckarsulm": {
        "key": "18adb00cb5135f6aa16b5fdea6dae2c63a507ae0f836540e",
        "idHouseNumber": 304,
        # "wasteTypes": ["28", "19", "31", "654"]
    },
    "Weinsberg": {
        "key": "18adb00cb5135f6aa16b5fdea6dae2c63a507ae0f836540e",
        "idHouseNumber": 353,
        # "wasteTypes": ["28", "19", "31", "654"]
    },
}
_LOGGER = logging.getLogger(__name__)

MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"
HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}


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
        idHouseNumber,
        wasteTypes=[],
    ):
        self._key = key
        self._idHouseNumber = idHouseNumber
        self._wasteTypes = wasteTypes  # list of integers
        self._ics = ICS()

    def fetch(self):
        # get token
        params = {"key": self._key, "modus": MODUS_KEY, "waction": "init"}

        r = requests.post("https://widgets.abfall.io/graphql",
                          params=params, headers=HEADERS)

        # add all hidden input fields to form data
        # There is one hidden field which acts as a token:
        # It consists of a UUID key and a UUID value.
        p = HiddenInputParser()
        p.feed(r.text)
        args = p.args

        args["idHouseNumber"] = self._idHouseNumber

        for i in range(len(self._wasteTypes)):
            args[f"f_id_abfalltyp_{i}"] = self._wasteTypes[i]

        args["wasteTypes_index_max"] = len(self._wasteTypes)
        args["wasteTypes"] = ",".join(
            map(lambda x: str(x), self._wasteTypes))

        now = datetime.datetime.now()
        date2 = now + datetime.timedelta(days=365)
        args["timeperiod"] = f"{now.strftime('%Y%m%d')}-{date2.strftime('%Y%m%d')}"

        params = {"key": self._key, "modus": MODUS_KEY,
                  "waction": "export_ics"}

        # get csv file
        r = requests.post(
            "https://widgets.abfall.io/graphql", params=params, data=args, headers=HEADERS
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

        dates = self._ics.convert(ics_file)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
