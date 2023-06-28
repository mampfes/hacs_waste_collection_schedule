import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS
from datetime import datetime

TITLE = "mags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR"
DESCRIPTION = "Source for Stadt Mönchengladbach"
URL = "https://mags.de"
COUNTRY = "de"
TEST_CASES = {
    "Schlossacker 43": {"street": "Schlossacker", "number": 43, "turnus": 2},
    "Azaleenweg 24": {"street": "Azaleenweg", "number": 24, "turnus": 2},
}

API_URL = "https://mags.de/fileadmin/ics/icscal.php"

ICON_MAP = {
    "Restmüll (Grau)": "mdi:trash-can",
    "Bioabfall (Braun)": "mdi:leaf",
    "Verpackungen (Gelb)": "mdi:recycle",
    "Altpapier (Blau)": "mdi:package-variant",
    "Papiermobil": "mdi:paper-roll",
    "Grünschnitt": "mdi:tree-outline",
    "Elektrokleingeräte-Sammlung": "mdi:radio",
}


class Source:
    def __init__(self, street, number, turnus=2):
        self._ics = ICS(split_at="/")
        self._street = street
        self._number = number
        self._turnus = turnus

    def fetch(self):
        # fetch the ical
        now = datetime.now()
        r = requests.get(API_URL,
                         params={"building_number": self._number,
                                 "building_number_addition": "",
                                 "street_name": self._street,
                                 "start_month": 1,
                                 "end_month": 12,
                                 "start_year": now.year,
                                 "end_year": now.year,
                                 "turnus": self._turnus
                                 }
                         )
        r.raise_for_status()

        # replace non-ascii character in UID, otherwise ICS converter will fail
        ics = ""
        for line in r.text.splitlines():
            if line.startswith("UID"):
                line = line.replace("ä", "ae")
                line = line.replace("ö", "oe")
                line = line.replace("ü", "ue")
            ics += line.replace("// GEM", "")
            ics += "\n"

        dates = self._ics.convert(ics)

        entries = []

        for d in dates:
            entries.append(
                Collection(
                    date=d[0],
                    t=d[1],
                    icon=ICON_MAP.get(d[1])
                )
            )

        return entries
