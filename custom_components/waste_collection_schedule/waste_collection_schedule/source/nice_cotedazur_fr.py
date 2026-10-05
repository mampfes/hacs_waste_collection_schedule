"""Source for waste collection schedules in Nice Côte d'Azur."""
from datetime import timedelta
import logging
from bs4 import BeautifulSoup
from waste_collection_schedule.source import Collection, WasteCollectionScheduleSource

_LOGGER = logging.getLogger(__name__)
URL = "https://www.nicecotedazur.org/services/dechets/collecte-et-tri-dechets/jours-et-horaires-de-collecte/"
SUPPORTED = {
    "Aspremont", "Beaulieu-sur-Mer", "Cap d'Ail", "Castagniers", "Colomars",
    "Èze", "Falicon", "La Trinité", "Le Broc", "Nice", "Saint-Blaise",
    "Saint-Jean-Cap-Ferrat", "Saint-Laurent-du-Var", "Saint-Martin-du-Var",
    "Villefranche-sur-Mer",
}


class Source(WasteCollectionScheduleSource):
    TITLE = "Nice Côte d'Azur (FR)"
    DESCRIPTION = "Collection schedules published by Métropole Nice Côte d'Azur."
    URL = URL
    TEST_CASES = {municipality: {"municipality": municipality} for municipality in sorted(SUPPORTED)}

    def fetch(self):
        municipality = self._municipality
        response = self._request.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        block = next((item for item in soup.select("div.collecte--block.commune")
                      if item.select_one(".entry-title") and
                      item.select_one(".entry-title").get_text(" ", strip=True) == municipality), None)
        if block is None:
            raise ValueError(f"Unknown municipality: {municipality}")
        if municipality not in SUPPORTED:
            _LOGGER.warning("%s is intentionally unsupported in Phase 1: alternating, seasonal, or sector-based schedule", municipality)
            return []
        text = block.select_one(".entry-content").get_text(" ", strip=True)
        schedules = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, "Vendredi": 4, "Samedi": 5, "Dimanche": 6}
        days = {weekday for weekday, number in schedules.items() if weekday.lower() in text.lower()}
        collections = []
        date = self._start_date
        while date <= self._end_date:
            if date.weekday() in {schedules[day] for day in days}:
                collections.append(Collection(date, "household waste"))
            date += timedelta(days=1)
        return collections
