import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "MZV Hegau"
DESCRIPTION = "Source for mzvhegau.de services for MZV Hegau, Germany."
URL = "https://www.mzvhegau.de"
COUNTRY = "de"
TEST_CASES = {
    "Engen": {"city": "Engen"},
    "Gai (Gailingen)": {"city": "Gai"},
    "GM (Gottmadingen)": {"city": "GM"},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Papier": Icons.PAPER,
    "Grünschnitt": Icons.GARDEN,
    "Christbaum": Icons.CHRISTMAS_TREE,
}

PARAM_TRANSLATIONS = {
    "en": {"city": "City"},
    "de": {"city": "Stadt/Gemeinde"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Your city or municipality shorthand, e.g. Engen, Gai, GM.",
    },
    "de": {
        "city": "Ihre Stadt oder Gemeinde (Kürzel), z.B. Engen, Gai, GM.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your city/municipality shorthand in the MZV Hegau service area.",
    "de": "Stadt/Gemeinde-Kürzel im MZV Hegau Verbandsgebiet eingeben.",
}

API_URL = "https://www.mzvhegau.de/wp-admin/admin-post.php?action=mzv_ics_download&slug={city}&whole_year=1&format=text"
PICKUPS_URL = "https://www.mzvhegau.de/wp-json/flexia/v2/pickups"

DATE_RE = re.compile(r"^(\d{2}\.\d{2}\.\d{4}):\s*(.+)$")


class Source:
    def __init__(self, city: str):
        self._city = city.strip()

    def _get_suggestions(self) -> list[str]:
        try:
            r = requests.get(PICKUPS_URL, timeout=10)
            r.raise_for_status()
            data = r.json()
            return [entry["shorthand"] for entry in data if "shorthand" in entry]
        except Exception:
            return []

    def fetch(self) -> list[Collection]:
        url = API_URL.format(city=self._city)
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        if "Ungültiger Ort" in r.text:
            suggestions = self._get_suggestions()
            raise SourceArgumentNotFoundWithSuggestions("city", self._city, suggestions)

        entries = []
        for line in r.text.splitlines():
            m = DATE_RE.match(line.strip())
            if not m:
                continue
            date_str, rest = m.group(1), m.group(2)
            date = datetime.strptime(date_str, "%d.%m.%Y").date()

            # Some lines have multiple collections separated by ", "
            for part in rest.split(", "):
                part = part.strip()
                # Strip leading emoji characters and whitespace
                while part and not part[0].isalpha():
                    part = part[1:].strip()
                if not part:
                    continue
                icon = ICON_MAP.get(part)
                entries.append(Collection(date=date, t=part, icon=icon))

        return entries
