"""SivomCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime
import logging
import re
import unicodedata
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
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

DAY_MAP = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}
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
    text: str | None, start: datetime.date, days_ahead: int = 365
) -> list[datetime.date]:
    if not text:
        return []
    cleaned = re.sub("\\s*\\(.*?\\)", "", text).strip()
    cleaned_lower = cleaned.lower()
    dates: list[datetime.date] = []
    end = start + datetime.timedelta(days=days_ahead)
    m = re.match("(\\w+)\\s+des\\s+semaines\\s+(impaires|paires)", cleaned_lower)
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
    m = re.match("tous\\s+les\\s+(\\w+)", cleaned_lower)
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
    m = re.match("(\\w+)\\s*[-–]\\s*(\\w+)", cleaned_lower)
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
    weekday = DAY_MAP.get(cleaned_lower)
    if weekday is not None:
        d = start
        while d <= end:
            if d.weekday() == weekday:
                dates.append(d)
            d += datetime.timedelta(days=1)
        return dates
    return []


class _CalendarClient:
    _session: Any

    def __init__(self, commune: str, street: str):
        self._commune = _strip_accents(commune.upper().strip())
        self._street = street.strip()

    def retrieve(self) -> Any:
        if self._commune not in COMMUNES:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, COMMUNES
            )
        _LOGGER.debug("Fetching collection data for %s", self._commune)
        params = {"action": "collectes_ville", "ville": self._commune}
        response = self._session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response

    def parse(self, response):
        data = response.json()
        if not data.get("success") or not data.get("data"):
            raise ValueError(f"No collection data found for commune '{self._commune}'")
        all_streets = [entry.get("rue", "") for entry in data["data"]]
        if not self._street:
            raise SourceArgumentRequiredWithSuggestions(
                "street",
                f"Please select a street in {self._commune}",
                sorted(all_streets),
            )
        street_lower = self._street.lower()
        match: dict | None = None
        for entry in data["data"]:
            if entry.get("rue", "").lower() == street_lower:
                match = entry
                break
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
        entries: list[dict] = []
        _LOGGER.debug(
            "Found street '%s': bac_vert=%s, bac_jaune=%s, bac_marron=%s",
            match.get("rue"),
            match.get("bac_vert"),
            match.get("bac_jaune"),
            match.get("bac_marron"),
        )
        for d in _parse_schedule(match.get("bac_vert"), today):
            entries.append({"date": d, "type": "Bac vert (Résiduels)"})
        for d in _parse_schedule(match.get("bac_jaune"), today):
            entries.append({"date": d, "type": "Bac jaune (Emballages)"})
        for d in _parse_schedule(match.get("bac_marron"), today):
            if (
                not (d.month == 12 and d.day >= 15)
                and d.month not in (1, 2)
                and (not (d.month == 3 and d.day < 15))
            ):
                entries.append({"date": d, "type": "Bac marron (Végétaux)"})
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
