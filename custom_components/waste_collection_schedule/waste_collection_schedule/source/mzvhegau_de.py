import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "MZV Hegau"
DESCRIPTION = "Source for mzvhegau.de services for MZV Hegau, Germany."
URL = "https://www.mzvhegau.de"
COUNTRY = "de"
TEST_CASES = {
    "Engen": {"city": "Engen"},
    "Singen": {"city": "Singen"},
}

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Gelber Sack": "mdi:recycle",
    "Papier": "mdi:newspaper",
    "Grünschnitt": "mdi:tree",
}

PARAM_TRANSLATIONS = {
    "en": {"city": "City"},
    "de": {"city": "Stadt/Gemeinde"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Your city or municipality name, e.g. Engen.",
    },
    "de": {
        "city": "Ihre Stadt oder Gemeinde, z.B. Engen.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your city/municipality in the " "MZV Hegau service area.",
    "de": "Stadt/Gemeinde im MZV Hegau " "Verbandsgebiet eingeben.",
}

API_URL = "https://www.mzvhegau.de/abfallkalender/{city}.ics"


class Source:
    def __init__(self, city: str):
        self._city = city.strip()
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        url = API_URL.format(city=self._city)
        r = requests.get(url)
        # Server returns 500 but with valid ICS content
        if not r.text.startswith("BEGIN:VCALENDAR"):
            r.raise_for_status()

        entries = []
        for date, name in self._ics.convert(r.text):
            # Strip "Abholung: " prefix and emoji
            clean = name
            if ": " in clean:
                clean = clean.split(": ", 1)[1]
            # Remove emoji prefix
            clean = clean.strip()
            while clean and not clean[0].isalpha():
                clean = clean[1:].strip()

            icon = ICON_MAP.get(clean)
            entries.append(Collection(date=date, t=clean, icon=icon))

        return entries
