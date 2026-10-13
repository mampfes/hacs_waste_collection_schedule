"""BonConseilCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
import html
import re
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

WASTE_TYPE_MAP = {
    "Collecte des ordures ménagères (bac noir)": "Ordures ménagères",
    "Collecte des matières organiques (bac brun)": "Matières organiques",
    "Collecte des matières recyclables (bac vert)": "Matières recyclables",
    "Collecte des matières recyclables (bac vert et bleu)": "Matières recyclables",
    "Collecte conteneur en métal – Déchets": "Conteneur en métal – Déchets",
    "Collecte conteneur en métal / Déchets": "Conteneur en métal – Déchets",
    "Collecte conteneur en métal – Recyclage": "Conteneur en métal – Recyclage",
    "Collecte conteneur en métal / Recyclage": "Conteneur en métal – Recyclage",
    "Collecte des encombrants": "Encombrants",
}
PAGE_URL = "https://villagebonconseil.ca/services-aux-citoyens/environnement/collecte-des-matieres-residuelles/"


class _CalendarClient:
    _session: Any

    def __init__(self):
        pass

    def retrieve(self) -> Any:
        r = self._session.get(PAGE_URL, timeout=30)
        r.raise_for_status()
        return r

    def parse(self, r):
        match = re.search("var eventscalendar\\s*=\\s*(\\[[\\s\\S]*?\\]);", r.text)
        if not match:
            raise ValueError("Could not find calendar data on the page")
        raw_data = match.group(1)
        entries = []
        pattern = "\\{[^{}]*'Date':\\s*new\\s*Date\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)[^{}]*'Title':\\s*'([^']*)'[^{}]*\\}"
        for m in re.finditer(pattern, raw_data):
            year = int(m.group(1))
            month = int(m.group(2)) + 1
            day = int(m.group(3))
            title_html = m.group(4)
            collection_date = datetime.date(year, month, day)
            title_match = re.search('title="([^"]*)"', title_html)
            if not title_match:
                continue
            raw_type = title_match.group(1)
            raw_type = html.unescape(raw_type)
            raw_type = raw_type.strip()
            waste_type = WASTE_TYPE_MAP.get(raw_type, raw_type)
            entries.append({"date": collection_date, "type": waste_type})
        if not entries:
            raise ValueError("No collection entries found")
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
