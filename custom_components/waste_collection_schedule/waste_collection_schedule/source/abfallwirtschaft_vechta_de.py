import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWB Abfallwirtschaft Vechta"
DESCRIPTION = "Source for AWB Abfallwirtschaft Vechta."
URL = "https://www.abfallwirtschaft-vechta.de/"
TEST_CASES = {
    "Vechta, An der Hasenweide": {"stadt": "Vechta", "strasse": "An der Hasenweide"},
    "Bakum, Up'n Sande": {"stadt": "Bakum", "strasse": "Up'n Sande"},
    "Neuenkirchen-Vörden, Braunschweiger Straße": {
        "stadt": "Neuenkirchen-Vörden",
        "strasse": "Braunschweiger Straße",
    },
    "Goldenstedt, An der Ellenbäke": {
        "stadt": "Goldenstedt",
        "strasse": "An der Ellenbäke",
    },
}


ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bioabfall": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
    "Altpapier": "mdi:package-variant",
    "Altpapier Siemer": "mdi:package-variant",
    "Altpapier Pamo": "mdi:package-variant",
    "Gelbe Tonne": "mdi:recycle",
}


class Source:
    def __init__(self, stadt: str, strasse: str):
        self._stadt: str = stadt
        self._strasse: str = strasse
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        entries = self.get_data(now.year)
        if now.month != 12:
            return entries
        try:
            return entries + self.get_data(now.year + 1)
        except Exception:
            pass

    def get_data(self, jahr):
        args = {"stadt": self._stadt, "strasse": self._strasse}

        collection_entries = []
        string_entries = []

        for papier_typ in ["pamo", "siemer"]:
            session = requests.Session()
            session.cookies.set("jahr", str(jahr))

            r = session.get(
                "https://www.abfallwirtschaft-vechta.de/CALENDER/inc.suche_stadt.php",
                params={"term": self._stadt},
            )
            r.raise_for_status()
            city_id = r.json()[0]["id"]
            session.cookies.set("stadt", str(city_id))

            r = session.get(
                "https://www.abfallwirtschaft-vechta.de/CALENDER/inc.suche_strasse.php",
                params={"stadt": city_id, "term": self._strasse},
            )
            r.raise_for_status()
            street = json.loads(r.text[1:-2])["strassen"][0]
            session.cookies.set("stadt", str(street["id"]))
            session.cookies.set("abfuhrbezirk", str(street["abfuhrbezirk"]))
            session.cookies.set("abfuhrbezirkpapir", str(street[papier_typ]))
            session.cookies.set("papier", papier_typ)

            args = {
                "stadt": city_id,
                "strasse": street["id"],
                "abfuhrbezirkpapier": street[papier_typ],
                "jahr": jahr,
                "papier": papier_typ,
                "trigger": "false",
                "triggerday": "false",
                "triggertime": "false",
            }

            r = session.get(
                "https://www.abfallwirtschaft-vechta.de/CALENDER/inc.get_calender_ics.php",
                params=args,
            )
            r.raise_for_status()
            r.encoding = "utf-8"

            # sometimes has a not ascii UID this would raise an Exception while converting
            dates = self._ics.convert(r.text.replace("UID:", "NOTUID: "))

            for d in dates:
                bin_type = (
                    d[1]
                    .replace("Abfuhrtermin", "")
                    .replace("Erinnerung", "")
                    .replace("für", "")
                    .strip()
                )

                if f"{bin_type} {str(d[0])}" in string_entries:
                    continue
                string_entries.append(f"{bin_type} {str(d[0])}")

                collection_entries.append(
                    Collection(
                        d[0],
                        bin_type,
                        ICON_MAP.get(
                            re.sub("[0-9]", "", bin_type).strip().replace("  ", " ")
                        ),
                    )
                )
        return collection_entries
