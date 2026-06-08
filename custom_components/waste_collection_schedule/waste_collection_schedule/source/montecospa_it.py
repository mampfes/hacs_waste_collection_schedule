import json
import urllib.parse
from datetime import date

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Monteco Spa"
DESCRIPTION = "Source for Monteco Spa waste collection (Puglia, Italy)."
URL = "https://www.montecospa.it"
COUNTRY = "it"

TEST_CASES = {
    "Lecce - zona centro storico (Domestica)": {
        "municipality": "Lecce",
        "zone": "zona_centro_storico",
    },
    "Lecce - zona_a (Non domestica)": {
        "municipality": "Lecce",
        "zone": "zona_a",
        "user_type": "Non domestica",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"municipality": "Municipality", "zone": "Zone", "user_type": "User type"},
    "it": {"municipality": "Comune", "zone": "Zona", "user_type": "Tipo utenza"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Name of the municipality exactly as listed on the Monteco website (e.g. 'Lecce').",
        "zone": "Zone name as shown in the URL/map on the Monteco website (e.g. 'zona_centro_storico').",
        "user_type": "Domestic or non-domestic user. One of 'Domestica' (default) or 'Non domestica'.",
    },
    "it": {
        "municipality": "Nome del comune esattamente come indicato sul sito Monteco (es. 'Lecce').",
        "zone": "Nome della zona come indicato nell'URL/mappa del sito Monteco (es. 'zona_centro_storico').",
        "user_type": "Utenza domestica o non domestica. Uno tra 'Domestica' (default) o 'Non domestica'.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.montecospa.it/it/servizi-evoluti?cta=calendario , click your address on the map, and note the municipality and zone shown in the results panel.",
    "it": "Visita https://www.montecospa.it/it/servizi-evoluti?cta=calendario , clicca sul tuo indirizzo sulla mappa e annota il comune e la zona mostrati nel pannello dei risultati.",
}

ICON_MAP = {
    "Carta": Icons.PAPER,
    "Imballaggi in cartone": Icons.PAPER,
    "Frazione organica": Icons.BIO_KITCHEN,
    "Frazione organica ecomobile": Icons.BIO_KITCHEN,
    "Plastica": Icons.PLASTIC_PACKAGING,
    "Vetro e metalli": Icons.GLASS,
    "Vetro e metalli ecomobile": Icons.GLASS,
    "Secco Residuo non riciclabile": Icons.GENERAL_WASTE,
    "Rifiuti Ingombranti e RAEE": Icons.BULKY,
    "Sfalci e potature": Icons.GARDEN,
    "Abiti usati": Icons.TEXTILE,
}

_PARSE_BASE = "https://montecospa.it:1337/parse"
_APP_ID = "0XUzreSqwbRPAVPzD1aFYLSLGSVafhnVwt2dkwi4"
_JS_KEY = "99ffdklUBn0m2azYI44f8ySFPeSGk2FqcvVlE1bC"
_MASTER_KEY = "99ffdklUBn0m2azYI44f8ySFPeSGk2FqcvVlE1Rq"

_HEADERS = {
    "X-Parse-Application-Id": _APP_ID,
    "X-Parse-Javascript-Key": _JS_KEY,
    "X-Parse-Master-Key": _MASTER_KEY,
}


class Source:
    def __init__(self, municipality: str, zone: str, user_type: str = "Domestica"):
        self._municipality = municipality
        self._zone = zone
        self._user_type = user_type

    def fetch(self) -> list[Collection]:
        where = {
            "serviceOnline": "1",
            "municipality": self._municipality,
            "serviceZoneName": self._zone,
            "serviceUserClass": self._user_type,
        }
        params = urllib.parse.urlencode({"where": json.dumps(where), "limit": 200})
        r = requests.get(
            f"{_PARSE_BASE}/classes/CityService?{params}",
            headers=_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        entries: list[Collection] = []
        for record in data.get("results", []):
            waste_type_obj = record.get("serviceWasteType") or {}
            waste_name = (
                waste_type_obj.get("name", "Unknown")
                if isinstance(waste_type_obj, dict)
                else "Unknown"
            )
            icon = ICON_MAP.get(waste_name)
            calendar = record.get("serviceCalendar") or []
            for day in calendar:
                if day.get("value") == "x":
                    try:
                        d = date.fromisoformat(day["date"])
                    except (ValueError, KeyError):
                        continue
                    entries.append(Collection(date=d, t=waste_name, icon=icon))

        return entries
