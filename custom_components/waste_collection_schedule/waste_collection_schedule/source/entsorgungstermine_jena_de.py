import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Entsorgungstermine Jena"
DESCRIPTION = "Daten von https://entsorgungstermine.jena.de/"
URL = "https://entsorgungstermine.jena.de/"
TEST_CASES = {
    "Mittelstraße 10":          {"strasse": "Mittelstraße", "hausnummer": "10"},
    "Altenburger Straße 15-19": {"strasse": "Altenburger Straße", "hausnummer": "15-19"},
}

ICON_MAP = {
    "Restabfall":       "mdi:trash-can",
    "Bioabfall":        "mdi:leaf",
    "Papier":           "mdi:package-variant",
    "Leichtverpackung": "mdi:recycle",
}

API_URL = "https://entsorgungstermine.jena.de/makeICSAll??x=true&{search}"
SEARCH_API_URL = API_URL.format(search="search/{search}")


class Source:
    def __init__(self, strasse: str, hausnummer: str | int):
        self._street: str = strasse
        self._hnummer: str | int = hausnummer
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        text = f"street={self._street}&hnummer={self._hnummer}"
        r = s.get(API_URL.format(search=text))
        r.raise_for_status()
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            icon = None
            for key, value in ICON_MAP.items():
                if icon:
                    continue
                if key in d[1]:
                    icon = value
            icon = "mdi:trash-can" if icon is None else icon
            entries.append(Collection(d[0], d[1], icon=icon))
        return entries
