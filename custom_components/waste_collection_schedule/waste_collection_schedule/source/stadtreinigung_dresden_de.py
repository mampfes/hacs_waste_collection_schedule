import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadtreinigung Dresden"
DESCRIPTION = "Source for Stadtreinigung Dresden waste collection."
URL = "https://www.dresden.de"
COUNTRY = "de"
TEST_CASES = {
    "Neumarkt 6": {"standort": 80542},
}

PARAM_TRANSLATIONS = {
    "en": {
        "standort": "Location ID",
    },
    "de": {
        "standort": "Standort-ID",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "standort": "Numeric location ID from the Dresden waste calendar URL (e.g. 80542 for Neumarkt 6).",
    },
    "de": {
        "standort": "Numerische Standort-ID aus der URL des Dresdner Abfallkalenders (z.B. 80542 für Neumarkt 6).",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://www.dresden.de/apps_ext/AbfallApp/wastebins and search for your address. Then download the PDF calendar — the URL will contain '?STANDORT=<number>'. Use that number as the Location ID.",
    "de": "Öffne https://www.dresden.de/apps_ext/AbfallApp/wastebins und suche deine Adresse. Lade den PDF-Kalender herunter — die URL enthält '?STANDORT=<Zahl>'. Diese Zahl ist die Standort-ID.",
}


class Source:
    def __init__(self, standort: int):
        self._standort = standort
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        now = datetime.datetime.now().date()

        r = requests.get(
            "https://stadtplan.dresden.de/project/cardo3Apps/IDU_DDStadtplan/abfall/ical.ashx",
            params={
                "STANDORT": self._standort,
                "DATUM_VON": now.strftime("%d.%m.%Y"),
                "DATUM_BIS": (now + datetime.timedelta(days=365)).strftime("%d.%m.%Y"),
            },
        )

        if not r.text.startswith("BEGIN:VCALENDAR"):
            raise SourceArgumentNotFound(
                "standort",
                self._standort,
            )

        dates = self._ics.convert(r.text)

        # example: "Leerung Gelbe Tonne, Bio-Tonne"

        entries = []
        for d in dates:
            if d[1] == "Abfallkalender endet bald":
                continue

            types = d[1].removeprefix("Leerung ")
            for type in types.split(", "):
                entries.append(Collection(d[0], type))
        return entries
