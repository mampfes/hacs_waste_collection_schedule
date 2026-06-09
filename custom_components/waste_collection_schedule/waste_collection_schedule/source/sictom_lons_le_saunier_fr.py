import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "SICTOM de Lons-le-Saunier"
DESCRIPTION = "Source for SICTOM de Lons-le-Saunier waste collection (Jura, France)."
URL = "https://sictom-lons-le-saunier.fr"
COUNTRY = "fr"

API_URL = "https://new-sictomlons.letri.com/graphql"

COMMUNES_QUERY = """
query SearchCommunes($search: String!) {
    communes(where: {search: $search}, first: 10) {
        nodes {
            title
            slug
            collecte_bac_bleu {
                frequenceBleu
                jourCollecteBleu
            }
            collecte_bac_gris {
                frequenceGris
                jourCollecteGris
            }
        }
    }
}
"""

COMMUNE_QUERY = """
query GetCommune($slug: ID!) {
    commune(id: $slug, idType: SLUG) {
        title
        slug
        collecte_bac_bleu {
            frequenceBleu
            jourCollecteBleu
        }
        collecte_bac_gris {
            frequenceGris
            jourCollecteGris
        }
    }
}
"""

# French day names to Python weekday number (Monday=0 ... Sunday=6)
FRENCH_DAYS = {
    "Lundi": 0,
    "Mardi": 1,
    "Mercredi": 2,
    "Jeudi": 3,
    "Vendredi": 4,
    "Samedi": 5,
    "Dimanche": 6,
}

TEST_CASES = {
    "Courbouzon": {"commune": "courbouzon"},
    "Lons-le-Saunier (Les Toupes)": {"commune": "lons-le-saunier-les-toupes"},
    "Saint Amour": {"commune": "saint-amour-les-ecarts"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "commune": "Commune",
    },
    "fr": {
        "commune": "Commune",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "commune": (
            "The slug of your commune (e.g. 'courbouzon'). "
            "Search on https://sictom-lons-le-saunier.fr/quand-passe-le-camion-benne.html "
            "to find your commune name, then convert to lowercase with hyphens."
        ),
    },
    "fr": {
        "commune": (
            "Le slug de votre commune (ex: 'courbouzon'). "
            "Cherchez votre commune sur https://sictom-lons-le-saunier.fr/quand-passe-le-camion-benne.html."
        ),
    },
}


def _is_parity_match(d: datetime.date, frequence: str) -> bool:
    """Return True if the ISO week number of date matches the required parity."""
    iso_week = d.isocalendar()[1]
    if frequence == "Paire":
        return iso_week % 2 == 0
    else:  # Impaire
        return iso_week % 2 == 1


def _generate_dates(
    days: list[str], frequence: str, today: datetime.date, lookahead_days: int = 365
) -> list[datetime.date]:
    """Generate all collection dates matching given French day names and week parity."""
    end_date = today + datetime.timedelta(days=lookahead_days)
    results = []

    for day_fr in days:
        weekday = FRENCH_DAYS.get(day_fr)
        if weekday is None:
            continue

        # Find the first occurrence of this weekday on or after today
        days_ahead = (weekday - today.weekday()) % 7
        current = today + datetime.timedelta(days=days_ahead)

        while current <= end_date:
            if _is_parity_match(current, frequence):
                results.append(current)
            current += datetime.timedelta(days=7)

    return results


class Source:
    def __init__(self, commune: str):
        self._commune = commune.strip().lower()

    def fetch(self) -> list[Collection]:
        # Try direct slug lookup first
        r = requests.post(
            API_URL,
            json={"query": COMMUNE_QUERY, "variables": {"slug": self._commune}},
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        data = r.json()

        commune_data = data.get("data", {}).get("commune")

        if commune_data is None:
            # Slug not found — search by name to offer suggestions
            r2 = requests.post(
                API_URL,
                json={
                    "query": COMMUNES_QUERY,
                    "variables": {"search": self._commune},
                },
                headers={"Content-Type": "application/json"},
            )
            r2.raise_for_status()
            search_data = r2.json()
            nodes = search_data.get("data", {}).get("communes", {}).get("nodes", [])
            suggestions = [n["slug"] for n in nodes]
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, suggestions
            )

        today = datetime.date.today()
        entries = []

        # Blue bin (bac bleu — recycling / emballages)
        bleu = commune_data.get("collecte_bac_bleu") or {}
        frequence_bleu = bleu.get("frequenceBleu")
        jours_bleu = bleu.get("jourCollecteBleu") or []
        if frequence_bleu and jours_bleu:
            for d in _generate_dates(jours_bleu, frequence_bleu, today):
                entries.append(Collection(date=d, t="Bac bleu", icon="mdi:recycle"))

        # Grey bin (bac gris — ordures ménagères)
        gris = commune_data.get("collecte_bac_gris") or {}
        frequence_gris = gris.get("frequenceGris")
        jours_gris = gris.get("jourCollecteGris") or []
        if frequence_gris and jours_gris:
            for d in _generate_dates(jours_gris, frequence_gris, today):
                entries.append(Collection(date=d, t="Bac gris", icon="mdi:trash-can"))

        return entries
