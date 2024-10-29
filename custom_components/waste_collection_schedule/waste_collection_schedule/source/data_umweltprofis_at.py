import logging
from datetime import datetime
from xml.dom.minidom import parseString

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Umweltprofis"
DESCRIPTION = "Source for Umweltprofis"
URL = "https://www.umweltprofis.at"
TEST_CASES = {
    "Ebensee": {
        "url": "https://data.umweltprofis.at/OpenData/AppointmentService/AppointmentService.asmx/GetIcalWastePickupCalendar?key=KXX_K0bIXDdk0NrTkk3xWqLM9-bsNgIVBE6FMXDObTqxmp9S39nIqwhf9LTIAX9shrlpfCYU7TG_8pS9NjkAJnM_ruQ1SYm3V9YXVRfLRws1"
    },
    "Rohrbach": {
        "xmlurl": "https://data.umweltprofis.at/opendata/AppointmentService/AppointmentService.asmx/GetTermineForLocationSecured?Key=TEMPKeyabvvMKVCic0cMcmsTEMPKey&StreetNr=118213&HouseNr=Alle&intervall=Alle"
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You need to generate your personal XML link before you can start using this source. Go to [https://data.umweltprofis.at/opendata/AppointmentService/index.aspx](https://data.umweltprofis.at/opendata/AppointmentService/index.aspx) and fill out the form. At the end at step 6 you get a link to a XML file. Copy this link use it as xmlurl parameter.",
    "de": "Sie müssen zuerst Ihren persönlichen XML-Link generieren, bevor Sie diese Quelle verwenden können. Gehen Sie zu [https://data.umweltprofis.at/opendata/AppointmentService/index.aspx](https://data.umweltprofis.at/opendata/AppointmentService/index.aspx) und füllen Sie das Formular aus. Am Ende von Schritt 6 erhalten Sie einen Link zu einer XML-Datei. Kopieren Sie diesen Link und verwenden Sie ihn als xmlurl-Parameter.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "url": "URL (Deprecated do not use)",
        "xmlurl": "XML URL",
    },
    "de": {
        "url": "URL (Veraltet nicht verwenden)",
        "xmlurl": "XML URL",
    },
}

_LOGGER = logging.getLogger(__name__)


def getText(element):
    s = ""
    for e in element.childNodes:
        if e.nodeType == e.TEXT_NODE:
            s += e.nodeValue
    return s


class Source:
    def __init__(self, url=None, xmlurl=None):
        self._url = url
        self._xmlurl = xmlurl
        self._ics = ICS()
        if url is None and xmlurl is None:
            raise Exception("either url or xmlurl needs to be specified")

    def fetch(self):
        if self._url is not None:
            return self.fetch_ics()
        elif self._xmlurl is not None:
            return self.fetch_xml()

    def fetch_ics(self):
        r = requests.get(self._url)
        r.raise_for_status()

        fixed_text = r.text.replace(
            "REFRESH - INTERVAL; VALUE = ", "REFRESH-INTERVAL;VALUE="
        )

        dates = self._ics.convert(fixed_text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries

    def fetch_xml(self):
        r = requests.get(self._xmlurl)
        r.raise_for_status()

        doc = parseString(r.text)
        appointments = doc.getElementsByTagName("AppointmentEntry")

        entries = []
        for a in appointments:
            date_string = getText(a.getElementsByTagName("Datum")[0])
            date = datetime.fromisoformat(date_string).date()
            waste_type = getText(a.getElementsByTagName("WasteType")[0])
            entries.append(Collection(date, waste_type))
        return entries
