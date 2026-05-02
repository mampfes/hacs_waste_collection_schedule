import xml.etree.ElementTree as ET
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Grand Besançon Métropole"
DESCRIPTION = (
    "Source for waste collection schedules in Grand Besançon Métropole, France."
)
URL = "https://www.grandbesancon.fr"
COUNTRY = "fr"

TEST_CASES = {
    "Amagney, Rue de Besancon 1": {
        "insee_code": "25014",
        "street": "Rue de Besancon",
        "house_number": "1",
    },
    "Besançon, chemin de la barre aux chevaux 1": {
        "insee_code": "25056",
        "street": "chemin de la barre aux chevaux",
        "house_number": "1",
    },
}

ICON_MAP = {
    "Ordures ménagères": "mdi:trash-can",
    "Tri sélectif": "mdi:recycle",
}

WASTE_TYPE_MAP = {
    "incinerable": "Ordures ménagères",
    "recyclable": "Tri sélectif",
}

DAY_MAP = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

STREETS_URL = "https://datasets.grandbesancon.fr/besanconfr.php"
COLLECTION_URL = "https://datasets.grandbesancon.fr/dechets.php"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your commune's INSEE code at https://www.insee.fr. Enter your street name as shown on the Grand Besançon waste calendar at https://data.grandbesancon.fr/opendata/dataset/joursDeCollecteDechets.",
    "fr": "Trouvez le code INSEE de votre commune sur https://www.insee.fr. Entrez le nom de votre rue tel qu'affiché sur le calendrier des déchets de Grand Besançon à https://data.grandbesancon.fr/opendata/dataset/joursDeCollecteDechets.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "insee_code": "5-digit INSEE code of your commune (e.g. 25014 for Amagney, 25056 for Besançon)",
        "street": "Street name as shown in the Grand Besançon system",
        "house_number": "House number (optional, helps filter results)",
    },
    "fr": {
        "insee_code": "Code INSEE à 5 chiffres de votre commune (ex : 25014 pour Amagney, 25056 pour Besançon)",
        "street": "Nom de la rue tel qu'affiché dans le système Grand Besançon",
        "house_number": "Numéro de rue (optionnel, aide à filtrer les résultats)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "insee_code": "INSEE Code",
        "street": "Street",
        "house_number": "House Number",
    },
    "fr": {
        "insee_code": "Code INSEE",
        "street": "Rue",
        "house_number": "Numéro",
    },
}


class Source:
    def __init__(
        self,
        insee_code: str,
        street: str,
        house_number: str | int | None = None,
    ):
        self._insee_code = str(insee_code).strip()
        self._street = street.strip()
        self._house_number = str(house_number).strip() if house_number else None

    def _resolve_street_code(self) -> str:
        params = {
            "method": "getRuesCommuneAction",
            "output": "json",
            "insee": self._insee_code,
        }
        r = requests.get(STREETS_URL, params=params, timeout=30)
        r.raise_for_status()
        streets = r.json()

        if not streets:
            raise SourceArgumentNotFound("insee_code", self._insee_code)

        for s in streets:
            if s["librueweb"].lower() == self._street.lower():
                return s["cdrue"]

        suggestions = [s["librueweb"] for s in streets]
        raise SourceArgumentNotFoundWithSuggestions("street", self._street, suggestions)

    def _fetch_collection_xml(self) -> ET.Element:
        params = {
            "method": "getJourDeCollecteDechetsParAdresseAction",
            "insee": self._insee_code,
        }
        if self._house_number:
            params["numrue"] = self._house_number
        r = requests.get(COLLECTION_URL, params=params, timeout=30)
        r.raise_for_status()
        return ET.fromstring(r.content)  # nosec B314

    def fetch(self) -> list[Collection]:
        cdrue = self._resolve_street_code()
        root = self._fetch_collection_xml()

        # Find the address matching our street code
        target_addr = None
        for addr in root.findall(".//adresse"):
            rue = addr.find("rue")
            if rue is not None and rue.get("id") == cdrue.lstrip("0"):
                num = addr.find("numero")
                if self._house_number and num is not None:
                    if num.text != self._house_number:
                        continue
                target_addr = addr
                break

        if target_addr is None:
            raise SourceArgumentNotFound("street", self._street)

        infos = target_addr.find("infosCollecte")
        if infos is None:
            return []

        today = date.today()
        end_date = today + timedelta(days=365)
        entries: list[Collection] = []

        for jour in infos.findall("jourDeCollecte"):
            waste_api_type = jour.get("type", "")
            semaine = jour.get("semaine")
            day_name = jour.text
            if not day_name:
                continue

            weekday = DAY_MAP.get(day_name.lower().strip())
            if weekday is None:
                continue

            waste_type = WASTE_TYPE_MAP.get(waste_api_type, waste_api_type)

            # Generate dates for this weekday
            d = today
            # Advance to the next occurrence of this weekday
            days_ahead = weekday - d.weekday()
            if days_ahead < 0:
                days_ahead += 7
            d = d + timedelta(days=days_ahead)

            while d <= end_date:
                iso_week = d.isocalendar()[1]
                include = True
                if semaine == "impaires" and iso_week % 2 == 0:
                    include = False
                elif semaine == "paires" and iso_week % 2 == 1:
                    include = False

                if include:
                    entries.append(
                        Collection(
                            date=d,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
                d += timedelta(weeks=1)

        return entries
