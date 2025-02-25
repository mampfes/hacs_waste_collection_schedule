# Nearly direct copy of source awn_de, awb_emsland_de

from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "GFA Lüneburg"
DESCRIPTION = "Source for GFA Lüneburg."
URL = "https://www.gfa-lueneburg.de/"
TEST_CASES = {
    "Dahlem Hauptstr. 7": {
        "city": "Dahlem",
        "street": "Hauptstr.",
        "house_number": 7,
    },
    "Wendish Evern Kückenbrook 5 A": {
        "city": "Wendish Evern",
        "street": "Kückenbrook",
        "house_number": "5 A",
    },
}
SERVLET = "https://portal.gfa-lueneburg.de:8443/WasteManagementLueneburg/WasteManagementServlet"

ICON_MAP = {
    "Restabfallbehaelter": "mdi:trash-can",
    "Restmuell": "mdi:trash-can",
    "Papiertonne": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
    "Gruenabfall": "mdi:leaf",
    "Biotonne": "mdi:leaf",
    "Sperrmuell Altmetall": "mdi:recycle",
}


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Make sure that the address exactly matches the one auto-completed by the website form: https://www.gfa-lueneburg.de/service/abfuhrkalender.html",
    "de": "Stellen Sie sicher, dass die Adresse genau der entspricht, die vom Website-Formular automatisch vervollständigt wird: https://www.gfa-lueneburg.de/service/abfuhrkalender.html",
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


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "house_number": "Hausnummer",
    }
}


class Source:
    def __init__(self, city: str, street: str, house_number: int | str):
        self._city = city
        self._street = street
        self._hnr = house_number
        self._ics = ICS()

    def fetch(self):
        session = requests.session()

        r = session.get(
            SERVLET,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "FALSE"},
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        parser = HiddenInputParser()
        parser.feed(r.text)

        args = parser.args
        args["Ort"] = self._city
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Method"] = "POST"
        args["SubmitAction"] = "CITYCHANGED"
        args["Focus"] = "Ort"
        r = session.post(
            SERVLET,
            data=args,
        )
        r.raise_for_status()

        args = parser.args
        args["Ort"] = self._city
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Method"] = "POST"
        args["SubmitAction"] = "STREETCHANGED"
        args["Focus"] = "Strasse"
        r = session.post(SERVLET, data=args)
        r.raise_for_status()

        args["SubmitAction"] = "forward"
        r = session.post(
            SERVLET,
            data=args,
        )
        r.raise_for_status()

        args["ApplicationName"] = (
            "com.athos.kd.lueneburg.WasteDisposalServicesBusinessCase"
        )
        args["SubmitAction"] = "filedownload_ICAL"
        args["IsLastPage"] = "true"
        args["Method"] = "POST"
        args["PageName"] = "Terminliste"
        del args["Ort"]
        del args["Strasse"]
        del args["Hausnummer"]
        r = session.post(
            SERVLET,
            data=args,
        )

        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            bin_type = d[1].strip()
            entries.append(Collection(d[0], bin_type, icon=ICON_MAP.get(bin_type)))

        return entries
