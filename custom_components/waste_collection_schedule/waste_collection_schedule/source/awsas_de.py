from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "AW SAS Burgenlandkreis"
DESCRIPTION = "Source for AW SAS (Abfallwirtschaft Sachsen-Anhalt Süd), serving Burgenlandkreis, Germany."
URL = "https://www.awsas.de"
COUNTRY = "de"
TEST_CASES = {
    "Elsteraue / Langendorf": {
        "municipality": "Gemeinde Elsteraue",
        "district": "Langendorf",
    },
    "Stadt Naumburg / Bad Kösen": {
        "municipality": "Stadt Naumburg",
        "district": "Bad Kösen",
    },
}

ICON_MAP = {
    "Restabfalltonne": Icons.GENERAL_WASTE,
    "Bioabfalltonne": Icons.ORGANIC,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Papiertonne": Icons.PAPER,
    "Gelber Abfallbehälter": Icons.PLASTIC_PACKAGING,
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "district": "District",
    },
    "de": {
        "municipality": "Gemeinde / Stadt",
        "district": "Ortsteil",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Name of the municipality (Gemeinde/Stadt), e.g. 'Gemeinde Elsteraue' or 'Stadt Naumburg'.",
        "district": "Name of the district (Ortsteil), e.g. 'Langendorf'.",
    },
    "de": {
        "municipality": "Name der Gemeinde oder Stadt, z. B. 'Gemeinde Elsteraue' oder 'Stadt Naumburg'.",
        "district": "Name des Ortsteils, z. B. 'Langendorf'.",
    },
}

API_URL = "https://www.awsas.de/pickups/lib/servlet.php"
ICS_URL = "https://www.awsas.de/pickups/ics.php"


class Source:
    def __init__(self, municipality: str, district: str) -> None:
        self._municipality = municipality
        self._district = district
        self._ics = ICS()

    def _get_location_id(self) -> str:
        """Resolve the district location UUID from municipality and district names."""
        r = requests.post(
            API_URL,
            data={
                "action": "requestLocations",
                "locationid": "",
                "jahre": "",
                "fractions": "",
            },
        )
        r.raise_for_status()
        root = r.json()

        municipality_locations = root.get("childs", [])
        municipality_map = {loc["name"]: loc["id"] for loc in municipality_locations}

        if self._municipality not in municipality_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, list(municipality_map.keys())
            )

        municipality_id = municipality_map[self._municipality]

        r = requests.post(
            API_URL,
            data={
                "action": "requestLocations",
                "locationid": municipality_id,
                "jahre": "",
                "fractions": "",
            },
        )
        r.raise_for_status()
        mun_data = r.json()

        district_locations = mun_data.get("childs", [])
        district_map = {loc["name"]: loc["id"] for loc in district_locations}

        if self._district not in district_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "district", self._district, list(district_map.keys())
            )

        return district_map[self._district]

    def fetch(self) -> list[Collection]:
        location_id = self._get_location_id()

        now = datetime.now()
        years = [str(now.year)]
        if now.month >= 11:
            years.append(str(now.year + 1))

        entries: list[Collection] = []
        seen_years: set[str] = set()

        for year in years:
            if year in seen_years:
                continue
            seen_years.add(year)

            r = requests.get(
                ICS_URL,
                params={
                    "locationid": location_id,
                    "jahre": year,
                    "fractions": "",
                },
            )
            r.raise_for_status()

            dates = self._ics.convert(r.text)
            for d in dates:
                icon = None
                for key, icon_value in ICON_MAP.items():
                    if d[1].startswith(key):
                        icon = icon_value
                        break
                entries.append(Collection(d[0], d[1], icon=icon))

        return entries
