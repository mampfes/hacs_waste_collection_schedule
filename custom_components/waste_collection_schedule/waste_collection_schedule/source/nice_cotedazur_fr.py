"""Source for waste collection schedules in Nice Côte d'Azur."""
from datetime import timedelta
import logging
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection
from waste_collection_schedule.source import BaseSource
from waste_collection_schedule.source_components import SourceResult
from waste_collection_schedule.source import WasteCollectionScheduleSource

_LOGGER = logging.getLogger(__name__)

URL = "https://www.nicecotedazur.org/services/dechets/collecte-et-tri-dechets/jours-et-horaires-de-collecte/"

SUPPORTED = {
    "Aspremont",
    "Beaulieu-sur-Mer",
    "Cap d'Ail",
    "Castagniers",
    "Colomars",
    "Èze",
    "Falicon",
    "La Trinité",
    "Le Broc",
    "Nice",
    "Saint-Blaise",
    "Saint-Jean-Cap-Ferrat",
    "Saint-Laurent-du-Var",
    "Saint-Martin-du-Var",
    "Villefranche-sur-Mer",
}


class Source(BaseSource):
    """Source for Nice Côte d'Azur waste collection schedules."""

    TITLE = "Nice Côte d'Azur (FR)"
    DESCRIPTION = "Collection schedules published by Métropole Nice Côte d'Azur."
    URL = URL

    TEST_CASES = {municipality: {"municipality": municipality} for municipality in sorted(SUPPORTED)}

    def fetch(self) -> SourceResult:
        """Fetch waste collection schedules for the specified municipality."""
        municipality = self._arg("municipality")

        if municipality not in SUPPORTED:
            raise ValueError(f"Unknown municipality: {municipality}")

        response = self._session.get(URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find the block for this municipality
        block = None
        for item in soup.select("div.collecte--block.commune"):
            title_elem = item.select_one(".entry-title")
            if title_elem and title_elem.get_text(" ", strip=True) == municipality:
                block = item
                break

        if block is None:
            raise ValueError(f"Municipality '{municipality}' not found on the website")

        # Extract schedule text
        content_elem = block.select_one(".entry-content")
        if not content_elem:
            return SourceResult([])

        text = content_elem.get_text(" ", strip=True)

        # Map days
        schedules = {
            "Lundi": 0,
            "Mardi": 1,
            "Mercredi": 2,
            "Jeudi": 3,
            "Vendredi": 4,
            "Samedi": 5,
            "Dimanche": 6,
        }

        # Find which days have collection
        days = {weekday for weekday, number in schedules.items() if weekday.lower() in text.lower()}

        # Build collections
        collections = []
        date = self._start_date
        while date <= self._end_date:
            if date.weekday() in {schedules[day] for day in days}:
                collections.append(Collection(date, "household waste"))
            date += timedelta(days=1)

        return SourceResult(collections)
