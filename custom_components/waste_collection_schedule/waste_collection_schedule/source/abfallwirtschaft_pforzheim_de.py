from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

# Source code based on rh_entsorgung_de.md
TITLE = "Abfallwirtschaft Pforzheim"
DESCRIPTION = "Source for Abfallwirtschaft Pforzheim."
URL = "https://www.abfallwirtschaft-pforzheim.de"
TEST_CASES = {
    "Abnobstraße": {
        "street": "Abnobastraße",
        "house_number": 3,
        "address_suffix": "",
    },
    "Im Buchbusch": {
        "street": "Im Buchbusch",
        "house_number": 12,
    },
    "Eisenbahnstraße": {
        "street": "Eisenbahnstraße",
        "house_number": 29,
        "address_suffix": "-33",
    },
}

ICON_MAP = {
    "Restmuell": "mdi:trash-can",
    "Biobehaelter": "mdi:leaf",
    "Papierbehaelter": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
    "Grossmuellbehaelter": "mdi:delete-circle",
}


API_URL = "https://onlineservices.abfallwirtschaft-pforzheim.de/WasteManagementPforzheim/WasteManagementServlet"

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
        args["Zeitraum"] = f"Jahresübersicht {year}"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["SubmitAction"] = "forward"
        args["ContainerGewaehltRM"] = "on"
        args["ContainerGewaehltBM"] = "on"
        args["ContainerGewaehltLVP"] = "on"
        args["ContainerGewaehltPA"] = "on"
        args["ContainerGewaehltPrMuell"] = "on"
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
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1].split(" ")[0])))
        return entries
