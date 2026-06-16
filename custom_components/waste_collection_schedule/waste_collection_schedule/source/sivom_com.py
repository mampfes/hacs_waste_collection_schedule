import datetime
import logging
import re
import unicodedata
from typing import Optional

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "SIVOM de la Vallée de l'Yerres et des Sénarts"
DESCRIPTION = "Source for waste collection schedules from the SIVOM de la Vallée de l'Yerres et des Sénarts (sivom.com)."
URL = "https://www.sivom.com"
COUNTRY = "fr"
TEST_CASES = {
    "Villecresnes": {"commune": "VILLECRESNES", "street": "ACACIAS Allée des"},
    "Brunoy": {"commune": "BRUNOY", "street": "ABBAYE rue de l"},
    "Yerres": {"commune": "YERRES", "street": "ABBAYE avenue de l'"},
}

API_URL = "https://api.sivom.com/optimus/signalements/api_villes.php"

COMMUNES = [
    "BOUSSY-SAINT-ANTOINE",
    "BRIE-COMTE-ROBERT",
    "BRUNOY",
    "COMBS-LA-VILLE",
    "CROSNE",
    "EPINAY-SOUS-SENART",
    "MANDRES-LES-ROSES",
    "MAROLLES-EN-BRIE",
    "MOISSY-CRAMAYEL",
    "PERIGNY-SUR-YERRES",
    "QUINCY-SOUS-SENART",
    "SANTENY",
    "VARENNES-JARCY",
    "VILLECRESNES",
    "YERRES",
]

ICON_MAP = {
    "Bac vert (Résiduels)": Icons.GENERAL_WASTE,
    "Bac jaune (Emballages)": Icons.RECYCLING,
    "Bac marron (Végétaux)": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to https://www.sivom.com/mesjoursdecollectes/?v=YOUR_COMMUNE to find your commune name and street name.",
    "fr": "Allez sur https://www.sivom.com/mesjoursdecollectes/?v=VOTRE_COMMUNE pour trouver le nom de votre commune et de votre rue.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "commune": "Name of the commune (e.g. VILLECRESNES, BRUNOY, YERRES)",
        "street": "Name of the street as shown on the SIVOM website",
    },
    "fr": {
        "commune": "Nom de la commune (ex: VILLECRESNES, BRUNOY, YERRES)",
        "street": "Nom de la rue tel qu'affiché sur le site du SIVOM",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "commune": "Commune",
        "street": "Street",
    },
    "fr": {
        "commune": "Commune",
        "street": "Rue",
    },
}

# French day names to weekday numbers (Monday=0)
DAY_MAP = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

# Plural forms for "Tous les ..." pattern
DAY_MAP_PLURAL = {
    "lundis": 0,
    "mardis": 1,
    "mercredis": 2,
    "jeudis": 3,
    "vendredis": 4,
    "samedis": 5,
    "dimanches": 6,
}


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")


def _get_iso_week_parity(d: datetime.date) -> str:
    return "odd" if d.isocalendar()[1] % 2 == 1 else "even"


def _parse_schedule(
    text: str, start: datetime.date, days_ahead: int = 365
) -> list[datetime.date]:
    if not text:
        return []

    # Strip parenthetical notes like "(avec YERRES)" or "(à partir du ...)"
    cleaned = re.sub(r"\s*\(.*?\)", "", text).strip()
    cleaned_lower = cleaned.lower()

    dates: list[datetime.date] = []
    end = start + datetime.timedelta(days=days_ahead)

    # Pattern: "Xxx des semaines IMPAIRES/PAIRES"
    m = re.match(r"(\w+)\s+des\s+semaines\s+(impaires|paires)", cleaned_lower)
    if m:
        day_name, parity = m.groups()
        weekday = DAY_MAP.get(day_name)
        if weekday is not None:
            target_parity = "odd" if parity == "impaires" else "even"
            d = start
            while d <= end:
                if d.weekday() == weekday and _get_iso_week_parity(d) == target_parity:
                    dates.append(d)
                d += datetime.timedelta(days=1)
            return dates

    # Pattern: "Tous les xxxs"
    m = re.match(r"tous\s+les\s+(\w+)", cleaned_lower)
    if m:
        day_name_plural = m.group(1)
        weekday = DAY_MAP_PLURAL.get(day_name_plural)
        if weekday is not None:
            d = start
            while d <= end:
                if d.weekday() == weekday:
                    dates.append(d)
                d += datetime.timedelta(days=1)
            return dates

    # Pattern: "Jour1 - Jour2" (two collection days per week)
    m = re.match(r"(\w+)\s*[-–]\s*(\w+)", cleaned_lower)
    if m:
        day1, day2 = m.groups()
        weekdays = []
        if day1 in DAY_MAP:
            weekdays.append(DAY_MAP[day1])
        if day2 in DAY_MAP:
            weekdays.append(DAY_MAP[day2])
        if weekdays:
            d = start
            while d <= end:
                if d.weekday() in weekdays:
                    dates.append(d)
                d += datetime.timedelta(days=1)
            return dates

    # Pattern: single day name "Jeudi"
    weekday = DAY_MAP.get(cleaned_lower)
    if weekday is not None:
        d = start
        while d <= end:
            if d.weekday() == weekday:
                dates.append(d)
            d += datetime.timedelta(days=1)
        return dates

    return []


class Source:
    def __init__(self, commune: str, street: str):
        self._commune = _strip_accents(commune.upper().strip())
        self._street = street.strip()

    def fetch(self) -> list[Collection]:
        if self._commune not in COMMUNES:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, COMMUNES
            )

        _LOGGER.debug("Fetching collection data for %s", self._commune)

        params = {
            "action": "collectes_ville",
            "ville": self._commune,
        }
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success") or not data.get("data"):
            raise Exception(f"No collection data found for commune '{self._commune}'")

        all_streets = [entry.get("rue", "") for entry in data["data"]]

        if not self._street:
            raise SourceArgumentRequiredWithSuggestions(
                "street",
                f"Please select a street in {self._commune}",
                sorted(all_streets),
            )

        # Find matching street (case-insensitive exact match first)
        street_lower = self._street.lower()
        match: Optional[dict] = None
        for entry in data["data"]:
            if entry.get("rue", "").lower() == street_lower:
                match = entry
                break

        # Fallback: partial match
        if match is None:
            for entry in data["data"]:
                if street_lower in entry.get("rue", "").lower():
                    match = entry
                    break

        if match is None:
            suggestions = [s for s in all_streets if street_lower in s.lower()]
            if not suggestions:
                suggestions = sorted(all_streets)
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, suggestions
            )

        today = datetime.date.today()
        entries: list[Collection] = []

        _LOGGER.debug(
            "Found street '%s': bac_vert=%s, bac_jaune=%s, bac_marron=%s",
            match.get("rue"),
            match.get("bac_vert"),
            match.get("bac_jaune"),
            match.get("bac_marron"),
        )

        for d in _parse_schedule(match.get("bac_vert"), today):
            entries.append(
                Collection(
                    d, "Bac vert (Résiduels)", icon=ICON_MAP["Bac vert (Résiduels)"]
                )
            )

        for d in _parse_schedule(match.get("bac_jaune"), today):
            entries.append(
                Collection(
                    d, "Bac jaune (Emballages)", icon=ICON_MAP["Bac jaune (Emballages)"]
                )
            )

        for d in _parse_schedule(match.get("bac_marron"), today):
            # Exclude mid-December to mid-March (no green waste collection)
            if (
                not (d.month == 12 and d.day >= 15)
                and d.month not in (1, 2)
                and not (d.month == 3 and d.day < 15)
            ):
                entries.append(
                    Collection(
                        d,
                        "Bac marron (Végétaux)",
                        icon=ICON_MAP["Bac marron (Végétaux)"],
                    )
                )

        return entries
