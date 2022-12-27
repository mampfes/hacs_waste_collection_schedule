import logging
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Burgenländischer Müllverband"
DESCRIPTION = "Source for BMV, Austria"
URL = "https://www.bmv.at"
TEST_CASES = {
    "Allersdorf": {"ort": "ALLERSDORF", "strasse": "HAUSNUMMER", "hausnummer": 9},
    "Bad Sauerbrunn": {
        "ort": "BAD SAUERBRUNN",
        "strasse": "BUCHINGERWEG",
        "hausnummer": 16,
    },
    "Rattersdorf": {
        "ort": "RATTERSDORF",
        "strasse": "SIEBENBRÜNDLGASSE",
        "hausnummer": 30,
    },
}

_LOGGER = logging.getLogger(__name__)


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
            if d["type"] == "HIDDEN":
                self._args[d["name"]] = d.get("value")


class Source:
    def __init__(self, ort, strasse, hausnummer):
        self._ort = ort
        self._strasse = strasse
        self._hausnummer = hausnummer
        self._ics = ICS()

    def fetch(self):
        session = requests.session()

        r = session.get(
            "https://webudb.udb.at/WasteManagementUDB/WasteManagementServlet?SubmitAction=wasteDisposalServices&InFrameMode=TRUE"
        )

        # add all hidden input fields to form data
        p = HiddenInputParser()
        p.feed(r.text)
        args = p.args

        args["Focus"] = "Ort"
        args["SubmitAction"] = "changedEvent"
        args["Ort"] = self._ort
        args["Strasse"] = "HAUSNUMMER"
        args["Hausnummer"] = 0
        r = session.post(
            "https://webudb.udb.at/WasteManagementUDB/WasteManagementServlet", data=args
        )

        args["Focus"] = "Strasse"
        args["SubmitAction"] = "changedEvent"
        args["Ort"] = self._ort
        args["Strasse"] = self._strasse
        args["Hausnummer"] = 0
        r = session.post(
            "https://webudb.udb.at/WasteManagementUDB/WasteManagementServlet", data=args
        )

        args["Focus"] = "Hausnummer"
        args["SubmitAction"] = "forward"
        args["Ort"] = self._ort
        args["Strasse"] = self._strasse
        args["Hausnummer"] = self._hausnummer
        r = session.post(
            "https://webudb.udb.at/WasteManagementUDB/WasteManagementServlet", data=args
        )

        args["ApplicationName"] = "com.athos.kd.udb.AbfuhrTerminModel"
        args["Focus"] = None
        args["IsLastPage"] = "true"
        args["Method"] = "POST"
        args["PageName"] = "Terminliste"
        args["SubmitAction"] = "filedownload_ICAL"
        del args["Ort"]
        del args["Strasse"]
        del args["Hausnummer"]
        r = session.post(
            "https://webudb.udb.at/WasteManagementUDB/WasteManagementServlet", data=args
        )

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
