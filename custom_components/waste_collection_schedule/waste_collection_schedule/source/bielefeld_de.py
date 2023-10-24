from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Bielefeld"
DESCRIPTION = "Source for Stadt Bielefeld."
URL = "https://bielefeld.de"
TEST_CASES = {
    "Umweltbetrieb": {
        "street": "Eckendorfer Straße",
        "house_number": 57,
    },
}

ICON_MAP = {
    "Restabfallbehaelter": "mdi:delete",
    "Bioabfallbehaelter": "mdi:leaf",
    "Papierbehaelter": "mdi:newspaper",
    "Wertstofftonne": "mdi:recycle",
}

SERVLET = "https://anwendungen.bielefeld.de/WasteManagementBielefeldTest/WasteManagementServlet"  # Actual Production URL changed from ORIGINAL_SERVLET
ORIGINAL_SERVLET = (
    "https://anwendungen.bielefeld.de/WasteManagementBielefeld/WasteManagementServlet"
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
        s = get_legacy_session()

        servlet = SERVLET

        r = s.get(
            servlet,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        )
        if r.status_code == 404:
            servlet = ORIGINAL_SERVLET
            r = s.get(
                servlet,
                params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
            )

        r.raise_for_status()
        r.encoding = "utf-8"

        parser = HiddenInputParser()
        parser.feed(r.text)

        args = parser.args
        args["Ort"] = self._street[0]
        args["Strasse"] = self._street
        args["Hausnummer"] = str(self._hnr)
        args["Hausnummerzusatz"] = self._suffix
        args["SubmitAction"] = "CITYCHANGED"
        args[
            "ApplicationName"
        ] = "com.athos.kd.bielefeld.abfuhrtermine.CheckAbfuhrTermineParameterBusinessCase"
        args["ContainerGewaehlt_1"] = "on"
        args["ContainerGewaehlt_2"] = "on"
        args["ContainerGewaehlt_3"] = "on"
        args["ContainerGewaehlt_4"] = "on"

        r = s.post(
            servlet,
            data=args,
        )

        r.raise_for_status()

        args["SubmitAction"] = "forward"
        r = s.post(
            servlet,
            data=args,
        )

        r.raise_for_status()

        reminder_day = "keine Erinnerung"  # "keine Erinnerung", "am Vortag", "2 Tage vorher", "3 Tage vorher"
        reminder_time = "18:00 Uhr"  # "XX:00 Uhr"

        args[
            "ApplicationName"
        ] = "com.athos.kd.bielefeld.abfuhrtermine.AbfuhrTerminModel"
        args["SubmitAction"] = "filedownload_ICAL"
        args["ICalErinnerung"] = reminder_day
        args["ICalZeit"] = reminder_time
        r = s.post(
            servlet,
            data=args,
        )

        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            bin_type = d[1].strip()
            if "Die neue ICal" in bin_type:
                continue

            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
