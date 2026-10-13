"""SivomCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime
import logging
import re
import unicodedata
from typing import Any

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Schedule
from waste_collection_schedule.retrievers import Request

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


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")


def _parse_schedule(
    text: str | None, start: datetime.date, key: str, days_ahead: int = 365
) -> list[Schedule]:
    """Read provider rules; the shared expander handles dates and ISO parity."""
    if not text:
        return []
    cleaned = re.sub(r"\s*\(.*?\)", "", text).strip().lower()
    parity = None
    match = re.match(r"(\w+)\s+des\s+semaines\s+(impaires|paires)", cleaned)
    if match:
        day_name, week_parity = match.groups()
        names = [day_name]
        parity = "odd" if week_parity == "impaires" else "even"
    elif match := re.match(r"tous\s+les\s+(\w+)", cleaned):
        names = [match.group(1).removesuffix("s")]
    elif match := re.match(r"(\w+)\s*[-–]\s*(\w+)", cleaned):
        names = list(match.groups())
    else:
        names = [cleaned]
    return [
        Schedule(
            key=key,
            start=recurrence.next_weekday(day, on_or_after=start),
            until=start + datetime.timedelta(days=days_ahead),
            iso_week_parity=parity,
        )
        for name in names
        if (day := recurrence.weekday(name)) is not None
    ]


def in_season(row, _source) -> bool:
    collection_date, label = row
    return label != "Bac marron (Végétaux)" or (3, 15) <= (
        collection_date.month,
        collection_date.day,
    ) < (12, 15)


class _CalendarClient:
    def __init__(self, commune: str, street: str):
        self._commune = _strip_accents(commune.upper().strip())
        self._street = street.strip()

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
        schedules = []
        for field, label in (
            ("bac_vert", "Bac vert (Résiduels)"),
            ("bac_jaune", "Bac jaune (Emballages)"),
            ("bac_marron", "Bac marron (Végétaux)"),
        ):
            schedules.extend(_parse_schedule(match.get(field), today, label))
        return schedules


class CalendarParser(Parser[list[Schedule]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[Schedule]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


def _request_params(commune: str, **_) -> dict:
    canonical = _strip_accents(commune.upper().strip())
    if canonical not in COMMUNES:
        raise SourceArgumentNotFoundWithSuggestions("commune", canonical, COMMUNES)
    return {"action": "collectes_ville", "ville": canonical}


calendar_retriever = Request(API_URL, params=_request_params, timeout=30)
