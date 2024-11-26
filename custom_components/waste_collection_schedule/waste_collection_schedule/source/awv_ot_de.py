from datetime import datetime
from urllib.parse import urlencode

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWV: Abfall Wirtschaftszweckverband Ostthüringen"
DESCRIPTION = "Source for AWV: Abfall Wirtschaftszweckverband Ostthüringen."
URL = "https://www.awv-ot.de/"
TEST_CASES = {
    "Bethenhausen Caasen 15A": {
        "city": "Bethenhausen OT Caasen",
        "street": "Caasen",
        "hnr": "15A",
    },
    "Kraftsdorf OT Oberndorf, Klosterlausnitzer Straße 5/1": {
        "city": "Kraftsdorf OT Oberndorf",
        "street": "Klosterlausnitzer Straße",
        "hnr": "5/1",
    },
    "Gera, Aga Birkenstraße 9": {
        "city": "Gera",
        "street": "Aga Birkenstraße",
        "hnr": "9",
    },
}


ICON_MAP = {
    "Hausmuelltonne": "mdi:trash-can",
    "Biotonne": "mdi:leaf",
    "Papiertonne": "mdi:package-variant",
    "Gelbe Tonne": "mdi:recycle",
}


API_URL = "https://www.awv-ot.de/tourenauskunft/auskunftbatix.php"
ICS_URL = "https://www.awv-ot.de/tourenauskunft/ics/ics.php"


class Source:
    def __init__(self, city: str, street: str, hnr: str):
        self._city: str = city
        self._street: str = street
        self._hnr: str = hnr
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        entries = self.fetch_year(now.year)
        if now.month == 12:
            try:
                entries.extend(self.fetch_year(now.year + 1))
            except Exception:
                pass
        return entries

    def fetch_year(self, year: int) -> list[Collection]:
        args = {
            "JAHR": str(year),
            "Ort": self._city,
            "Strasse": self._street,
            "Step": "3",
            "HSN": self._hnr,
        }

        session = requests.Session()
        r = session.post(
            API_URL,
            data=urlencode(args, encoding="latin-1"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        r = session.get(ICS_URL)
        r.raise_for_status()
        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            bin_type = d[1].removeprefix("Leerung").strip()
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        if not entries:
            raise Exception(
                "No entries found Make sure the address matches exactly with an address suggested here: https://www.awv-ot.de/www/awvot/abfuhrtermine/leerungstage/"
            )

        return entries
