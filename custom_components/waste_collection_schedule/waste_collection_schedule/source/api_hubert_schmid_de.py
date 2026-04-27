from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "HubertSchmid Recycling und Umweltschutz GmbH"
TITLE_LANG = "de"
DESCRIPTION = "Abfuhrtermine Blaue Tonne"
URL = "https://www.hschmid24.de/BlaueTonne/"
API_URL = "https://www.hschmid24.de/BlaueTonne/php/ajax.php"

TEST_CASES = {
    "Albatsried(Seeg)": {"city": "Albatsried(Seeg)"},
    "Nesselwang > Attlesee": {"city": "Nesselwang", "district": "Attlesee"},
    "Buchloe > Hausen > Dorfstraße": {
        "city": "Buchloe",
        "district": "Hausen",
        "street": "Dorfstraße",
    },
}


class Source:
    def __init__(
        self,
        city: str,
        district: str | None = None,
        street: str | None = None,
    ):
        self._city = city
        self._ortsteil = district
        self._strasse = street

    def fetch(self):
        r = requests.post(
            f"{API_URL}",
            data={"l": 3, "p1": self._city, "p2": self._ortsteil, "p3": self._strasse},
        )

        r.raise_for_status()
        calendarEntries = r.json()["cal"]

        entries = []
        for entry in calendarEntries:
            if entry != "0000-00-00":
                entries.append(
                    Collection(
                        date=datetime.strptime(entry, "%Y-%m-%d").date(),
                        t="Blaue Tonne",
                        icon="mdi:package-variant",
                    )
                )

        return entries
