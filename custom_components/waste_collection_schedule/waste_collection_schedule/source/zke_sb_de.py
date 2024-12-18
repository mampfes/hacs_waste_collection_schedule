from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS


# Source code based on abfallwirtschaft_pforzheim_de
TITLE = "ZKE Saarbrücken"
DESCRIPTION = "Source for Zentraler Kommunaler Entsorgungsbetrieb (ZKE) Saarbrücken."
URL = "https://www.zke-sb.de"
TEST_CASES = {
    "Harthweg": {
        "street": "Harthweg",
        "house_number": 7,
    },
    "Jahnweg": {
        "street": "Jahnweg",
        "house_number": 6,
    },
    "Netzbachtal": {
        "street": "Netzbachtal",
        "house_number": 1,
    },
}

ICON_MAP = {
    "Restmuell:": "mdi:trash-can",
    "Biomuell": "mdi:leaf",
    "Papiertonne": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
}


API_URL = "https://info.zke-sb.de/WasteManagementSaarbruecken/WasteManagementServlet"

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
    def __init__(self, street: str, house_number: str):
        self._street = street
        self._hnr = house_number
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
        args["SubmitAction"] = "CITYCHANGED"
        args["Zeitraum"] = f"Jahresübersicht {year}"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["SubmitAction"] = "STREETCHANGED"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["SubmitAction"] = "forward"
        args["ContainerGewaehlt_1"] = "on"
        args["ContainerGewaehlt_2"] = "on"
        args["ContainerGewaehlt_3"] = "on"
        args["ContainerGewaehlt_4"] = "on"
        args["ContainerGewaehlt_5"] = "on"
        args["ContainerGewaehlt_6"] = "on"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args["ApplicationName"] = "com.athos.kd.saarbruecken.AbfuhrTerminModel"
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
