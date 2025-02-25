from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "RESO"
DESCRIPTION = "Source for RESO."
URL = "https://reso-gmbh.de"
TEST_CASES = {
    "Reichelsheim Kerngemeinde": {"ort": "Reichelsheim", "ortsteil": "Kerngemeinde"}
}


ICON_MAP = {
    "restmüll": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "biotonne": "mdi:leaf",
    "papiertonne": "mdi:package-variant",
    "gelber-sack": "mdi:recycle",
}


EXTRA_INFO = [
    {"title": "Bad-König", "default_params": {"ort": "Bad-König"}},
    {"title": "Brensbach", "default_params": {"ort": "Brensbach"}},
    {"title": "Breuberg", "default_params": {"ort": "Breuberg"}},
    {"title": "Brombachtal", "default_params": {"ort": "Brombachtal"}},
    {"title": "Erbach", "default_params": {"ort": "Erbach"}},
    {"title": "Fränkisch-Crumbach", "default_params": {"ort": "Fränkisch-Crumbach"}},
    {"title": "Höchst", "default_params": {"ort": "Höchst"}},
    {"title": "Lützelbach", "default_params": {"ort": "Lützelbach"}},
    {"title": "Michelstadt", "default_params": {"ort": "Michelstadt"}},
    {"title": "Mossautal", "default_params": {"ort": "Mossautal"}},
    {"title": "Oberzent", "default_params": {"ort": "Oberzent"}},
    {"title": "Reichelsheim", "default_params": {"ort": "Reichelsheim"}},
]


API_URL = "https://reso-gmbh.abfallkalender.services/php/Kalender-2-ICS.php"


class Source:
    def __init__(self, ort: str, ortsteil: str):
        self._ort: str = ort
        self._ortsteil: str = ortsteil
        self._ics = ICS(split_at=r" \+ ")

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        entries = self.get_data(now.year)
        if now.month == 12:
            try:
                entries.extend(self.get_data(now.year + 1))
            except Exception:
                pass
        return entries

    def get_data(self, year):
        args = {
            "Ort": self._ort,
            "Ortsteil": self._ortsteil,
            "Jahr": year,
            "art": 1,
            "downOderurl2": "Semikolon",
        }

        # get json file
        r = requests.post(API_URL, data=args)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1].lower())))

        return entries
