from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "HubertSchmid Recycling und Umweltschutz GmbH"
DESCRIPTION = "Abfuhrtermine Blaue Tonne"
URL = "https://www.hschmid24.de/BlaueTonne/"
API_URL = "https://www.hschmid24.de/BlaueTonne/php/ajax.php"

class Source:
    def __init__(
        self,
        city: str | None = None,
        ortsteil: str | None = None,
        strasse: str | None = None,
    ):
        self._city = city
        self._ortsteil = ortsteil
        self._strasse = strasse

    def fetch(self):
        r = requests.post(
            f"{API_URL}", data={"l": 3, "p1": self._city, "p2": self._ortsteil, "p3": self._strasse}
        )

        r.raise_for_status()
        calendarEntries = r.json()["cal"]

        entries = []
        for entry in calendarEntries:
            if entry != "0000-00-00":
                entries.append(Collection(date=datetime.strptime(entry, '%Y-%m-%d').date(), t="Blaue Tonne", icon="mdi:package-variant"))

        return entries