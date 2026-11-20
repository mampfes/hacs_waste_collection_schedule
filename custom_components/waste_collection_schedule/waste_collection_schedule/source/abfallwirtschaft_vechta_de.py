import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
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
    "Restabfall": Icons.GENERAL_WASTE,
    "Glass": Icons.GLASS,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Altpapier Siemer": Icons.PAPER,
    "Altpapier Pamo": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
}


# ids of the "staedte" options embedded in the calendar page (the 10 municipalities of the county)
CITY_IDS = {
    "Bakum": 1,
    "Damme": 2,
    "Dinklage": 3,
    "Goldenstedt": 4,
    "Holdorf": 5,
    "Lohne": 6,
    "Neuenkirchen-Vörden": 7,
    "Steinfeld": 8,
    "Vechta": 9,
    "Visbek": 10,
}

API_URL = "https://www.abfallwirtschaft-vechta.de/index.php"


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
            next_year = self.get_data(now.year + 1)
        except Exception:
            return entries
        # the next year's calendar may not be published yet, then the current one is returned again
        seen = {(e.date, e.type) for e in entries}
        return entries + [e for e in next_year if (e.date, e.type) not in seen]

    def get_street(self) -> dict:
        city_id = next(
            (
                cid
                for name, cid in CITY_IDS.items()
                if name.lower() == self._stadt.lower()
            ),
            None,
        )
        if city_id is None:
            # the old city search matched a prefix, so keep accepting one that names a single city
            prefixed = [
                cid
                for name, cid in CITY_IDS.items()
                if name.lower().startswith(self._stadt.strip().lower())
            ]
            if self._stadt.strip() and len(prefixed) == 1:
                city_id = prefixed[0]
        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "stadt", self._stadt, CITY_IDS.keys()
            )

        r = requests.get(
            API_URL,
            params={
                "option": "com_abfuhrkalender",
                "task": "proxy.strassen",
                "format": "json",
                "stadt": city_id,
                "q": self._strasse,
            },
        )
        r.raise_for_status()
        streets = r.json()["data"]
        if not streets:
            raise SourceArgumentNotFound("strasse", self._strasse)
        return next(
            (s for s in streets if s["name"].lower() == self._strasse.lower()),
            streets[0],
        )

    def get_data(self, jahr):
        street = self.get_street()

        collection_entries = []
        string_entries = []

        # the paper provider is chosen by the user on the website, so fetch every one available for the street
        for papier_typ in ["pamo", "siemer"]:
            if not street.get(papier_typ):
                continue

            r = requests.get(
                API_URL,
                params={
                    "option": "com_abfuhrkalender",
                    "task": "proxy.ics",
                    "strasse": street["id"],
                    "jahr": jahr,
                    "papier": papier_typ,
                },
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

                if f"{bin_type} {d[0]!s}" in string_entries:
                    continue
                string_entries.append(f"{bin_type} {d[0]!s}")

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
