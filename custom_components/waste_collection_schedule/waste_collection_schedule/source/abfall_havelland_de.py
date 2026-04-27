# There was an ICS source but the ICS file was not stored permanently and would be removed after a few days.
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallbehandlungsgesellschaft Havelland mbH (abh)"
TITLE_LANG = "de"
DESCRIPTION = "Source for Abfallbehandlungsgesellschaft Havelland mbH."
URL = "https://abfall-havelland.de/"
TEST_CASES = {
    "Wustermark Drosselgasse": {
        "city": "Wustermark",
        "street": "Drosselgasse",
    },
    "Milow Friedhofstr.": {"city": "Milow", "street": "Friedhofstr."},
    "Falkensee Ahornstr.": {"city": "Falkensee", "street": "Ahornstr."},
    "Falkensee complex street name": {
        "city": "Falkensee",
        "street": "Karl-Marx-Str. (von Friedrich-Hahn-Str. bis Am Schlaggraben)",
    },
}

ICON_MAP = {
    "mülltonne": "mdi:trash-can",
    "bio-tonne": "mdi:leaf",
    "papier": "mdi:package-variant",
    "gelbe": "mdi:recycle",
}

API_URL = "https://www.abfall-havelland.de/ics.php"


class Source:
    def __init__(self, city: str, street: str):
        self._ort: str = city
        self._strasse: str = street
        self._ics = ICS(split_at=", ")

    def fetch(self) -> list[Collection]:
        args = {"city": self._ort, "street": self._strasse}

        # ics content
        r = requests.get(API_URL, params=args)
        r.raise_for_status()
        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            bin_type = d[1].replace(" - Abholtermin", "")
            entries.append(
                Collection(d[0], bin_type, ICON_MAP.get(bin_type.split()[0].lower()))
            )

        return entries
