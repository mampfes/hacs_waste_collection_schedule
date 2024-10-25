from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

# Source code based on rh_entsorgung_de.md
TITLE = "Bamberg (City/Stadt)"
DESCRIPTION = "Source for Bamberg (City/Stadt)."
URL = "https://www.stadt.bamberg.de"


TEST_CASES = {
    "Gartenstraße 2": {
        "street": "Gartenstraße",
        "house_number": 2,
    },
    "Egelseestraße 41b": {
        "street": "Egelseestraße",
        "house_number": 114,
        "address_suffix": "a",
    },
}

ICON_MAP = {
    "Restmuell": "mdi:trash-can",
    "Biomuell": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelber": "mdi:recycle",
}


API_URL = (
    "https://ebbweb.stadt.bamberg.de/WasteManagementBamberg/WasteManagementServlet"
)

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
            if str(d["type"]).lower() == "hidden":
                self._args[d["name"]] = d["value"] if "value" in d else ""


class Source:
    def __init__(self, street: str, house_number: int, address_suffix: str = ""):
        self._street = street
        self._hnr = house_number
        self._suffix = address_suffix
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        entries = self.get_data(now.year)
        if now.month == 12:
            try:
                entries += self.get_data(now.year + 1)
            except Exception:
                pass
        return entries

    def get_data(self, year):
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
        args["Ort"] = self._street[0].upper()
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._suffix
        args["SubmitAction"] = "CITYCHANGED"
        # args["Zeitraum"] = f"Jahresübersicht {year}"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["SubmitAction"] = "forward"
        for i in range(1, 10):
            args[f"ContainerGewaehlt_{i}"] = "on"
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
                Collection(d[0], d[1].strip(), ICON_MAP.get(d[1].strip().split()[0]))
            )
        return entries
