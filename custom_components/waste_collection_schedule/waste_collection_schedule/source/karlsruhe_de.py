from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "City of Karlsruhe"
DESCRIPTION = "Source for City of Karlsruhe."
URL = "https://www.karlsruhe.de/"
TEST_CASES = {
    "Östliche Rheinbrückenstraße 1": {
        "street": "Östliche Rheinbrückenstraße",
        "hnr": 1,
    },
    "Habichtweg 4": {"street": "Habichtweg", "hnr": 4},
    "Machstraße 5": {"street": "Machstraße", "hnr": 5},
    "Bernsteinstraße 10 ladeort 1": {
        "street": "Bernsteinstraße",
        "hnr": 10,
        "ladeort": 1,
    },
    "Bernsteinstraße 10 ladeort 2": {
        "street": "Bernsteinstraße",
        "hnr": 10,
        "ladeort": 2,
    },
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Wertstoff": "mdi:recycle",
    "Sperrmüllabholung": "mdi:wardrobe",
}


API_URL = "https://web6.karlsruhe.de/service/abfall/akal/akal_{year}.php"


class Source:
    def __init__(self, street: str, hnr: str | int, ladeort: int | None = None):
        self._street: str = street
        self._hnr: str | int = hnr
        self._ladeort: int | None = ladeort
        self.ics = ICS()

    def fetch(self):
        now = datetime.now()
        error = None
        for year in (now.year, now.year + 1, now.year - 1):
            try:
                return self.get_data(API_URL.format(year=year))
            except Exception as e:
                error = e
        raise error

    def get_data(self, url):
        data = {
            "strasse_n": self._street,
            "hausnr": self._hnr,
            "ical": "+iCalendar",
            "ladeort": self._ladeort,
        }
        params = {"hausnr": self._hnr}

        r = requests.post(url, data=data, params=params)
        dates = self.ics.convert(r.text)

        entries = []
        for d in dates:
            date, waste_type = d
            waste_type = waste_type.split(",")[0]
            icon = ICON_MAP.get(waste_type)
            entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
