from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

# Source code based on rh_entsorgung_de.md
TITLE = "Bonn Orange"
DESCRIPTION = "Source for Bonn Orange."
URL = "https://www.bonnorange.de"
TEST_CASES = {
    "Adenauerallee 4": {
        "street": "Adenauerallee",
        "house_number": 4,
        "address_suffix": "",
    },
    "Baumschulallee 1": {
        "street": "Baumschulallee",
        "house_number": 1,
    },
    "Baumschulallee 43 A": {
        "street": "Baumschulallee",
        "house_number": 43,
        "address_suffix": "A",
    },
}

ICON_MAP = {
    "Restabfallbehaelter": "mdi:trash-can",
    "Bioabfallbehaelter": "mdi:leaf",
    "Papierbehaelter": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
    "Grossmuellbehaelter": "mdi:delete-circle",
    "Weihnachtsbaeume": "mdi:pine-tree",
    "Sperrmuell": "mdi:sofa",
}

API_URL = "https://www5.bonn.de/WasteManagementBonnOrange/WasteManagementServlet"

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
        args["Ajax"] = "TRUE"
        args["Focus"] = "Ort"
        args["Hausnummer"] = ""
        args["Hausnummerzusatz"] = ""
        args["Ort"] = self._street[0].upper()
        args["Strasse"] = ""
        args["SubmitAction"] = "CITYCHANGED"
        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        args = parser.args
        args["Ajax"] = "false"
        args["Focus"] = "Hausnummer"
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._suffix
        args["Ort"] = self._street[0].upper()
        args["Strasse"] = self._street
        args["SubmitAction"] = "forward"

        r = session.post(
            API_URL,
            data=args,
        )
        r.raise_for_status()

        parser.feed(r.text)
        args = parser.args
        args["Ajax"] = "TRUE"
        args["Focus"] = ""
        args["IsLastPage"] = "true"
        args["PageName"] = "Terminliste"
        args["SubmitAction"] = "filedownload_ICAL"
        del args["Hausnummer"]
        del args["Hausnummerzusatz"]
        del args["Ort"]
        del args["Strasse"]

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
