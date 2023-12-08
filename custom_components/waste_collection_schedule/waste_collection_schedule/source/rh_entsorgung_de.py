from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Rhein-Hunsrück Entsorgung (RHE)"
DESCRIPTION = "Source for RHE (Rhein Hunsrück Entsorgung)."
URL = "https://www.rh-entsorgung.de"
TEST_CASES = {
    "Horn": {
        "city": "Rheinböllen",
        "street": "Erbacher Straße",
        "house_number": 13,
        "address_suffix": "A",
    },
    "Bärenbach": {
        "city": "Bärenbach",
        "street": "Schwarzener Straße",
        "house_number": 10,
    },
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
            if str(d["type"]).lower() == "hidden":
                self._args[d["name"]] = d["value"] if "value" in d else ""


class Source:
    def __init__(
        self, city: str, street: str, house_number: int, address_suffix: str = ""
    ):
        self._city = city
        self._street = street
        self._hnr = house_number
        self._suffix = address_suffix
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        entries = self.get_entries(now.year)
        if now.month == 12:
            entries += self.get_entries(now.year + 1)
        return entries

    def get_entries(self, year):
        session = requests.session()

        r = session.get(
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet",
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        parser = HiddenInputParser()
        parser.feed(r.text)

        args = parser.args
        args["Ort"] = self._city
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._suffix
        args["SubmitAction"] = "CITYCHANGED"
        args["Zeitraum"] = f"Jahresübersicht {year}"

        r = session.post(
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet",
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
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet",
            data=args,
        )
        r.raise_for_status()

        args["ApplicationName"] = "com.athos.kd.rheinhunsrueck.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"
        r = session.post(
            "https://aao.rh-entsorgung.de/WasteManagementRheinhunsrueck/WasteManagementServlet",
            data=args,
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
