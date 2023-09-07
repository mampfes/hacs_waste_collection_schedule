# mostly copied from abfallwirtschaft_pforzheim_de.py
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Ravensburg"
DESCRIPTION = "Source for Landkreis Ravensburg."
URL = "https://www.rv.de/"
TEST_CASES = {
    "Altshausen Altshauser Weg 1 ": {
        "ort": "Altshausen",
        "strasse": "Altshauser Weg",
        "hnr": 1,
        "hnr_zusatz": "",
    },
    "Hoßkirch, Ob den Gärten 1": {
        "ort": "Hoßkirch",
        "strasse": "Ob den Gärten",
        "hnr": "1",
        "hnr_zusatz": "",
    },
    "Bad Kreznach, Steubenstraße 5645A": {
        "ort": "bAd KrezNach",
        "strasse": "steuBenstraße",
        "hnr": 5645,
        "hnr_zusatz": "A",
    },
}


ICON_MAP = {
    "Restmuelltonne": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Papiertonne": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
}


API_URL = "https://athos-onlinedienste.rv.de/WasteManagementRavensburgPrivat/WasteManagementServlet"


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
            if str(d["type"]).lower() == "hidden":
                self._args[d["name"]] = d["value"] if "value" in d else ""


class Source:
    def __init__(self, ort: str, strasse: str, hnr: str | int, hnr_zusatz: str | int):
        self._ort: str = ort
        self._strasse: str = strasse
        self._hnr: str | int = hnr
        self._hnr_zusatz: str | int = hnr_zusatz
        self._ics = ICS()

    def fetch(self):
        session = requests.session()

        r = session.get(
            API_URL,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        parser = HiddenInputParser()
        parser.feed(r.text)

        args = parser.args
        args["Ort"] = self._ort
        args["Strasse"] = self._strasse
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._hnr_zusatz
        args["SubmitAction"] = "CITYCHANGED"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["SubmitAction"] = "forward"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["ApplicationName"] = "com.athos.nl.mvc.abfterm.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"

        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(
                Collection(d[0], d[1].strip(), ICON_MAP.get(d[1].split(" ")[0]))
            )
        return entries
