import datetime
import logging

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

_LOGGER = logging.getLogger(__name__)

TITLE = "Toulouse Métropole"
DESCRIPTION = "Source pour la collecte des déchets de Toulouse Métropole (37 communes)."
URL = "https://data.toulouse-metropole.fr"
COUNTRY = "fr"

TEST_CASES = {
    "Colomiers - Avenue Henri Guillaumet": {
        "street_name": "Avenue Henri Guillaumet",
    },
    "Toulouse - Rue de la Paix": {
        "street_name": "Rue de la Paix",
    },
    # Confirmed in dataset: collecte sélective "semaine paire" (bi-weekly)
    "Chemin Vié (bi-weekly CS)": {
        "street_name": "Chemin Vié",
    },
    # Confirmed in dataset: ordures ménagères "Vendredi"
    "Route de Fonbeauzard": {
        "street_name": "Route de Fonbeauzard",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street name exactly as it appears on the Toulouse Métropole open data portal. "
        "You can look it up at: "
        "https://data.toulouse-metropole.fr/explore/dataset/dechets-collecte-des-ordures-menageres/table/"
    ),
    "fr": (
        "Saisissez le nom de votre voie tel qu'il apparaît sur le portail open data de Toulouse Métropole. "
        "Vous pouvez le retrouver ici : "
        "https://data.toulouse-metropole.fr/explore/dataset/dechets-collecte-des-ordures-menageres/table/"
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_name": "Name of your street, exactly as in the open data portal (e.g. 'Avenue Henri Guillaumet')",
    },
    "fr": {
        "street_name": "Nom de votre voie, tel qu'il apparaît dans le portail open data (ex : 'Avenue Henri Guillaumet')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"street_name": "Street name"},
    "fr": {"street_name": "Nom de la voie"},
}

_WASTE_TYPE_MAP = {
    "Ordure ménagère": "Déchets non recyclables",
    "Collecte sélective": "Déchets recyclables",
}

ICON_MAP = {
    "Déchets non recyclables": Icons.GENERAL_WASTE,
    "Déchets recyclables": Icons.RECYCLING,
}

# ── Opendatasoft API v2.1 ──────────────────────────────────────────────────────
_BASE = "https://data.toulouse-metropole.fr/api/explore/v2.1/catalog/datasets"
_OM_DATASET = "dechets-collecte-des-ordures-menageres"
_CS_DATASET = "dechets-collecte-selective"

# French weekday names → Python weekday (Monday=0)
_DAY_MAP: dict[str, int] = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

# How many weeks ahead to generate dates
_WEEKS_AHEAD = 8


def _parse_schedule(infobulle: str) -> tuple[int | None, str | None]:
    """
    Parse the 'infobulle_pdi' field into (weekday, frequency).

    Examples:
      "Vendredi"               -> (4, None)       every week
      "Mercredi semaine paire" -> (2, "even")      even ISO weeks
      "Lundi semaine impaire"  -> (0, "odd")       odd ISO weeks

    Returns (weekday_int, frequency) where frequency is None / "even" / "odd".
    """
    value = infobulle.lower().strip()

    frequency = None
    if "semaine paire" in value:
        frequency = "even"
        value = value.replace("semaine paire", "").strip()
    elif "semaine impaire" in value:
        frequency = "odd"
        value = value.replace("semaine impaire", "").strip()

    weekday = _DAY_MAP.get(value)
    return weekday, frequency


def _generate_dates(
    weekday: int, frequency: str | None, weeks: int = _WEEKS_AHEAD
) -> list[datetime.date]:
    """
    Generate upcoming collection dates for a given weekday + frequency.
    """
    today = datetime.date.today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    first = today + datetime.timedelta(days=days_ahead)

    dates = []
    for i in range(weeks):
        candidate = first + datetime.timedelta(weeks=i)
        iso_week = candidate.isocalendar()[1]

        if frequency is None:
            dates.append(candidate)
        elif frequency == "even" and iso_week % 2 == 0:
            dates.append(candidate)
        elif frequency == "odd" and iso_week % 2 != 0:
            dates.append(candidate)

    return dates


class Source:
    def __init__(self, street_name: str):
        self._street_name = street_name.strip()

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []

        for dataset in (_OM_DATASET, _CS_DATASET):
            entries.extend(self._fetch_dataset(dataset))

        if not entries:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name",
                self._street_name,
                [],
            )
        return entries

    def _fetch_dataset(self, dataset: str) -> list[Collection]:
        url = f"{_BASE}/{dataset}/records"
        params = {
            "limit": 20,
            "refine": f'libelle_voie:"{self._street_name}"',
            "select": "libelle_voie,infobulle_pdi,flux",
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        records = response.json().get("results", [])

        entries: list[Collection] = []
        seen: set[tuple[int, str | None]] = set()  # deduplicate (weekday, frequency)

        for record in records:
            infobulle = (record.get("infobulle_pdi") or "").strip()
            flux = (record.get("flux") or "").strip()

            if not infobulle or not flux:
                continue

            weekday, frequency = _parse_schedule(infobulle)
            if weekday is None:
                _LOGGER.debug("Could not parse day from: %r", infobulle)
                continue

            key = (weekday, frequency)
            if key in seen:
                continue
            seen.add(key)

            waste_type = _WASTE_TYPE_MAP.get(flux, flux)
            icon = ICON_MAP.get(waste_type, Icons.GENERAL_WASTE)

            for date in _generate_dates(weekday, frequency):
                entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
