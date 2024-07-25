from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "KWU Entsorgung Landkreis Oder-Spree"
DESCRIPTION = "Source for KWU Entsorgung, Germany"
URL = "https://www.kwu-entsorgung.de/"
TEST_CASES = {
    "Erkner": {"city": "Erkner", "street": "Heinrich-Heine-Straße", "number": "11"},
    "Bad Saarow": {"city": "Bad Saarow", "street": "Ahornallee", "number": 1},
    "Spreenhagen Feldweg 4": {"city": "Spreenhagen", "street": "Feldweg", "number": 4},
}

HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}
ICON_MAP = {
    "Restabfall": "mdi:trash-can-outline",
    "Gelber Sack": "mdi:recycle",
    "Papiertonne": "mdi:package-variant",
    "Biotonne": "mdi:food-apple-outline",
}


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "number": "Hausnummer",
    }
}


class Source:
    def __init__(self, city, street, number):
        self._city = city.strip().lower()
        self._street = street.strip().lower()
        self._number = str(number).lower().strip()
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        r = requests.get(
            "https://kalender.kwu-entsorgung.de", headers=HEADERS, verify=True
        )

        parsed_html = BeautifulSoup(r.text, "html.parser")
        Orte = parsed_html.find_all("option")

        OrtValue = None
        for Ort in Orte:
            if self._city == Ort.text.strip().lower():
                OrtValue = Ort["value"]
                break
        if OrtValue is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, [o.text.strip() for o in Orte]
            )

        r = requests.get(
            "https://kalender.kwu-entsorgung.de/kal_str2ort.php",
            params={"ort": OrtValue},
            headers=HEADERS,
            verify=True,
        )

        parsed_html = BeautifulSoup(r.text, "html.parser")
        Strassen = parsed_html.find_all("option")

        StrasseValue = None
        for Strasse in Strassen:
            if self._street == Strasse.text.strip().lower():
                StrasseValue = Strasse["value"]
                break
        if StrasseValue is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, [s.text.strip() for s in Strassen]
            )

        r = requests.get(
            "https://kalender.kwu-entsorgung.de/kal_str2ort.php",
            params={"ort": OrtValue, "strasse": StrasseValue},
            headers=HEADERS,
            verify=True,
        )

        parsed_html = BeautifulSoup(r.text, "html.parser")
        objects = parsed_html.find_all("option")

        ObjektValue = None
        for obj in objects:
            if self._number == obj.text.lower().strip():
                ObjektValue = obj["value"]
                break
        if ObjektValue is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "number", self._number, [o.text.strip() for o in objects]
            )

        r = requests.post(
            "https://kalender.kwu-entsorgung.de/kal_uebersicht-2023.php",
            data={
                "ort": OrtValue,
                "strasse": StrasseValue,
                "objekt": ObjektValue,
                "jahr": date.today().year,
            },
            headers=HEADERS,
            verify=True,
        )

        parsed_html = BeautifulSoup(r.text, "html.parser")
        Links = parsed_html.find_all("a")

        for Link in Links:
            if "ICal herunterladen" in Link.text:
                ics_url = Link["href"]

        if ics_url is None:
            raise Exception("ics url not found")

        if "kwu.lokal" in ics_url:
            ics_url = ics_url.replace(
                "http://kalender.kwu.lokal", "https://kalender.kwu-entsorgung.de"
            )

        # get ics file
        r = session.get(ics_url, headers=HEADERS, verify=True)
        r.raise_for_status()

        # parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        # for d in dates:
        #    entries.append(Collection(d[0], d[1]))
        # return entries
        for d in dates:
            waste_type = d[1].strip()
            next_pickup_date = d[0]

            entries.append(
                Collection(
                    date=next_pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
