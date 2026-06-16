import logging
from datetime import datetime
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ICS import ICS

TITLE = "UBZ Umwelt- und Servicebetrieb Zweibrücken"
DESCRIPTION = "Source for UBZ Zweibrücken waste collection."
URL = "https://www.ubzzw.com"
COUNTRY = "de"
TEST_CASES = {
    "Vogesenstraße 75": {"street": "Vogesenstraße", "house_number": "75"},
    "Lindenstraße 5": {"street": "Lindenstraße", "house_number": "5"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "house_number": "House number",
    },
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Full street name as shown on the UBZ collection calendar (e.g. Vogesenstraße)",
        "house_number": "House number, optionally including a suffix (e.g. 75 or 1 a)",
    },
    "de": {
        "street": "Vollständiger Straßenname wie im UBZ-Abfallkalender angegeben (z.B. Vogesenstraße)",
        "house_number": "Hausnummer, optional mit Zusatz (z.B. 75 oder 1 a)",
    },
}

_LOGGER = logging.getLogger(__name__)

API_URL = (
    "https://leerungen.ubzzw.com/WasteManagementZweibruecken/WasteManagementServlet"
)

ICON_MAP = {
    "Restabfalltonne": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Papiertonne": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Problemstoff": Icons.HAZARDOUS,
}


class HiddenInputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._args = {}

    @property
    def args(self):
        return self._args

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "input":
            d = dict(attrs)
            if str(d.get("type", "")).lower() == "hidden":
                name = d.get("name", "")
                value = d.get("value", "")
                if name:
                    self._args[name] = value


class Source:
    def __init__(self, street: str, house_number: str):
        self._street = street
        self._house_number = str(house_number)
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        entries = self._get_data(now.year)
        if now.month == 12:
            try:
                entries += self._get_data(now.year + 1)
            except Exception:
                pass
        return entries

    def _get_data(self, year: int):
        session = requests.Session()

        r = session.get(
            API_URL,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        parser = HiddenInputParser()
        parser.feed(r.text)
        args = parser.args

        street_letter = self._street[0].upper()
        args["Ort"] = street_letter
        args["Strasse"] = self._street
        args["Hausnummer"] = self._house_number
        args["Hausnummerzusatz"] = ""
        args["SubmitAction"] = "CITYCHANGED"
        args["Zeitraum"] = f"Jahresübersicht {year}"

        r = session.post(API_URL, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        parser2 = HiddenInputParser()
        parser2.feed(r.text)
        args = parser2.args

        args["Ort"] = street_letter
        args["Strasse"] = self._street
        args["Hausnummer"] = self._house_number
        args["Hausnummerzusatz"] = ""
        args["SubmitAction"] = "STREETCHANGED"
        args["Zeitraum"] = f"Jahresübersicht {year}"

        r = session.post(API_URL, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        parser3 = HiddenInputParser()
        parser3.feed(r.text)
        args = parser3.args

        args["Ort"] = street_letter
        args["Strasse"] = self._street
        args["Hausnummer"] = self._house_number
        args["Hausnummerzusatz"] = ""
        args["SubmitAction"] = "forward"
        args["Zeitraum"] = f"Jahresübersicht {year}"

        r = session.post(API_URL, data=args)
        r.raise_for_status()
        r.encoding = "utf-8"

        parser4 = HiddenInputParser()
        parser4.feed(r.text)
        args = parser4.args

        if args.get("PageName") != "Terminliste":
            raise SourceArgumentNotFound(
                "street or house_number",
                f"{self._street} {self._house_number}",
            )

        args["ApplicationName"] = "com.athos.nl.mvc.abfterm.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"

        r = session.post(API_URL, data=args)
        r.raise_for_status()

        ics_text = r.content.decode("utf-8")
        dates = self._ics.convert(ics_text)

        entries = []
        for d in dates:
            waste_type = d[1].strip()
            icon = None
            for key, icon_value in ICON_MAP.items():
                if key in waste_type:
                    icon = icon_value
                    break
            entries.append(Collection(d[0], waste_type, icon))

        return entries
