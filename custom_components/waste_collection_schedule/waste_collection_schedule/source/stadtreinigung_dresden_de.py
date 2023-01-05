import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadtreinigung Dresden"
DESCRIPTION = "Source for Stadtreinigung Dresden waste collection."
URL = "https://www.dresden.de"
TEST_CASES = {
    "Neumarkt 6": {"standort": 80542},
}


class Source:
    def __init__(self, standort):
        self._standort = standort
        self._ics = ICS()

    def fetch(self):

        now = datetime.datetime.now().date()

        r = requests.get(
            "https://stadtplan.dresden.de/project/cardo3Apps/IDU_DDStadtplan/abfall/ical.ashx",
            params={
                "STANDORT": self._standort,
                "DATUM_VON": now.strftime("%d.%m.%Y"),
                "DATUM_BIS": (now + datetime.timedelta(days=365)).strftime("%d.%m.%Y"),
            },
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
