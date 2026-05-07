from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Câmara Municipal de Lisboa"
DESCRIPTION = "Source for waste collection schedules in Lisboa, Portugal."
URL = "https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo"
COUNTRY = "pt"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo and search for your address on the map. The area name shown in the popup (e.g. 'Restelo', 'Madredeus') is the value to use.",
}

TEST_CASES = {
    "Restelo": {"area_name": "Restelo"},
    "Madredeus": {"area_name": "Madredeus"},
    "Alvito": {"area_name": "Alvito"},
    "Campo Ourique": {"area_name": "Campo Ourique"},
}

ICON_MAP = {
    "Indiferenciado": "mdi:trash-can",
    "Papel e Cartão": "mdi:newspaper-variant-outline",
    "Embalagens": "mdi:recycle",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "area_name": "Name of the collection area (e.g. 'Restelo', 'Madredeus'). Visit https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo to find your area.",
    },
    "de": {
        "area_name": "Name des Sammelgebiets (z.B. 'Restelo', 'Madredeus'). Besuchen Sie https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo um Ihr Gebiet zu finden.",
    },
    "fr": {
        "area_name": "Nom de la zone de collecte (ex. 'Restelo', 'Madredeus'). Visitez https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo pour trouver votre zone.",
    },
    "it": {
        "area_name": "Nome dell'area di raccolta (es. 'Restelo', 'Madredeus'). Visita https://informacoeseservicos.lisboa.pt/servicos/dias-do-lixo per trovare la tua area.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "area_name": "Collection Area",
    },
    "de": {
        "area_name": "Sammelgebiet",
    },
    "fr": {
        "area_name": "Zone de collecte",
    },
    "it": {
        "area_name": "Area di raccolta",
    },
}

API_URL = "https://services.arcgis.com/1dSrzEWVQn5kHHyK/ArcGIS/rest/services/Amb_Reciclagem/FeatureServer/7/query"

# Portuguese weekday abbreviations to Python weekday (0=Monday ... 6=Sunday)
PT_WEEKDAYS = {
    "2ª": 0,  # Segunda-feira (Monday)
    "3ª": 1,  # Terça-feira (Tuesday)
    "4ª": 2,  # Quarta-feira (Wednesday)
    "5ª": 3,  # Quinta-feira (Thursday)
    "6ª": 4,  # Sexta-feira (Friday)
    "Sáb": 5,  # Sábado (Saturday)
    "Dom": 6,  # Domingo (Sunday)
}


def _parse_days(days_str: str) -> list[int]:
    """Parse Portuguese weekday string into list of Python weekday integers."""
    if not days_str or days_str.strip() == "":
        return []
    weekdays = []
    for part in days_str.replace("feira", "").split(","):
        part = part.strip()
        if part in PT_WEEKDAYS:
            weekdays.append(PT_WEEKDAYS[part])
    return weekdays


def _generate_dates(weekdays: list[int], weeks: int = 26) -> list[date]:
    """Generate collection dates for the given weekdays over N weeks."""
    today = date.today()
    dates = []
    for weekday in weekdays:
        days_ahead = (weekday - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)
        for i in range(weeks):
            dates.append(next_date + timedelta(weeks=i))
    return sorted(dates)


class Source:
    def __init__(self, area_name: str):
        self._area_name = area_name.strip()

    def fetch(self) -> list[Collection]:
        safe_name = self._area_name.replace("'", "''")
        params = {
            "where": f"NOME = '{safe_name}'",
            "outFields": "NOME,DIAS_IND,DIAS_PAPEL,DIAS_EMBAL",
            "returnGeometry": "false",
            "f": "json",
        }

        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()

        data = r.json()
        features = data.get("features", [])

        if not features:
            # Fetch available area names for suggestions
            suggestions = self._get_area_names()
            raise SourceArgumentNotFoundWithSuggestions(
                "area_name", self._area_name, suggestions
            )

        attrs = features[0]["attributes"]

        entries: list[Collection] = []

        # Indiferenciado (mixed/undifferentiated waste)
        ind_days = _parse_days(attrs.get("DIAS_IND", ""))
        for d in _generate_dates(ind_days):
            entries.append(
                Collection(date=d, t="Indiferenciado", icon=ICON_MAP["Indiferenciado"])
            )

        # Papel e Cartão (paper and cardboard)
        papel_days = _parse_days(attrs.get("DIAS_PAPEL", ""))
        for d in _generate_dates(papel_days):
            entries.append(
                Collection(date=d, t="Papel e Cartão", icon=ICON_MAP["Papel e Cartão"])
            )

        # Embalagens (packaging)
        embal_days = _parse_days(attrs.get("DIAS_EMBAL", ""))
        for d in _generate_dates(embal_days):
            entries.append(
                Collection(date=d, t="Embalagens", icon=ICON_MAP["Embalagens"])
            )

        return entries

    @staticmethod
    def _get_area_names() -> list[str]:
        """Fetch all available area names for suggestions."""
        params = {
            "where": "DIAS_IND <> ' '",
            "outFields": "NOME",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "orderByFields": "NOME",
            "f": "json",
        }
        try:
            r = requests.get(API_URL, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            return sorted(
                {
                    f["attributes"]["NOME"]
                    for f in data.get("features", [])
                    if f["attributes"].get("NOME")
                }
            )
        except Exception:
            return []
