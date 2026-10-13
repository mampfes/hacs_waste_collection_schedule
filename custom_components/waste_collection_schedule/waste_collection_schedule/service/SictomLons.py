"""SictomLons calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

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
FRENCH_DAYS = {
    "Lundi": 0,
    "Mardi": 1,
    "Mercredi": 2,
    "Jeudi": 3,
    "Vendredi": 4,
    "Samedi": 5,
    "Dimanche": 6,
}


def _is_parity_match(d: datetime.date, frequence: str) -> bool:
    """Return True if the ISO week number of date matches the required parity."""
    iso_week = d.isocalendar()[1]
    if frequence == "Paire":
        return iso_week % 2 == 0
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
        days_ahead = (weekday - today.weekday()) % 7
        current = today + datetime.timedelta(days=days_ahead)
        while current <= end_date:
            if _is_parity_match(current, frequence):
                results.append(current)
            current += datetime.timedelta(days=7)
    return results


def _retrieve(source: BaseSource) -> Any:
    r = source.session.post(
        API_URL,
        json={
            "query": COMMUNE_QUERY,
            "variables": {"slug": source.params["commune"].strip().lower()},
        },
        headers={"Content-Type": "application/json"},
    )
    r.raise_for_status()
    data = r.json()
    commune_data = data.get("data", {}).get("commune")
    if commune_data is None:
        r2 = source.session.post(
            API_URL,
            json={
                "query": COMMUNES_QUERY,
                "variables": {"search": source.params["commune"].strip().lower()},
            },
            headers={"Content-Type": "application/json"},
        )
        r2.raise_for_status()
        search_data = r2.json()
        nodes = search_data.get("data", {}).get("communes", {}).get("nodes", [])
        suggestions = [n["slug"] for n in nodes]
        raise SourceArgumentNotFoundWithSuggestions(
            "commune", source.params["commune"].strip().lower(), suggestions
        )
    return commune_data


def _parse(source: BaseSource, commune_data) -> list[dict[str, Any]]:
    today = datetime.date.today()
    entries = []
    bleu = commune_data.get("collecte_bac_bleu") or {}
    frequence_bleu = bleu.get("frequenceBleu")
    jours_bleu = bleu.get("jourCollecteBleu") or []
    if frequence_bleu and jours_bleu:
        for d in _generate_dates(jours_bleu, frequence_bleu, today):
            entries.append({"date": d, "type": "Bac bleu"})
    gris = commune_data.get("collecte_bac_gris") or {}
    frequence_gris = gris.get("frequenceGris")
    jours_gris = gris.get("jourCollecteGris") or []
    if frequence_gris and jours_gris:
        for d in _generate_dates(jours_gris, frequence_gris, today):
            entries.append({"date": d, "type": "Bac gris"})
    return entries


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
