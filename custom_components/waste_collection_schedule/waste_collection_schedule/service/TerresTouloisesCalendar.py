"""TerresTouloisesCalendar retrieval and parsing, using the pipeline HTTP session."""

import re
import unicodedata
from datetime import date, timedelta
from typing import Any

from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

DATA_URL = "https://www.terrestouloises.com/terres-touloises-au-quotidien/gestion-des-dechets/collectes-des-ordures-menageres-et-recyclables/"
COMMUNES = [
    "Aingeray",
    "Andilly",
    "Ansauville",
    "Avrainville",
    "Bicqueley",
    "Bois-de-Haye",
    "Boucq",
    "Bouvron",
    "Bruley",
    "Charmes-la-Côte",
    "Chaudeney-sur-Moselle",
    "Choloy-Ménillot",
    "Domèvre-en-Haye",
    "Domgermain",
    "Dommartin-lès-Toul",
    "Écrouves",
    "Fontenoy-sur-Moselle",
    "Foug",
    "Francheville",
    "Gondreville",
    "Grosrouvres",
    "Gye",
    "Jaillon",
    "Lagney",
    "Laneuveville-derrière-Foug",
    "Lay-Saint-Rémy",
    "Lucey",
    "Manoncourt-en-Woëvre",
    "Manonville",
    "Ménil-la-Tour",
    "Minorville",
    "Noviant-aux-Prés",
    "Pagney-derrière-Barine",
    "Pierre-la-Treiche",
    "Royaumeix",
    "Sanzey",
    "Tremblecourt",
    "Trondes",
    "Villey-le-Sec",
    "Villey-Saint-Étienne",
]


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _normalize_commune(s: str) -> str:
    """Remove accents, uppercase, and collapse separators for fuzzy name matching."""
    s = _strip_accents(s)
    return re.sub("[-'’ ]", "", s.upper())


COMMUNES_NORMALIZED = {_normalize_commune(c): c for c in COMMUNES}

WEEKDAY_MAP = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}
MOIS_MAP = {
    "janvier": 1,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
}
EXCEPTION_PATTERN = re.compile(
    "(\\d{1,2})(?:er)?\\s+([a-zA-Zàâäéèêëïîôöùûüÿçñ]+)(?:\\s+(\\d{4}))?\\s+report[ée]e?\\s+au\\s+(\\d{1,2})(?:er)?\\s+([a-zA-Zàâäéèêëïîôöùûüÿçñ]+)\\s+(\\d{4})",
    re.IGNORECASE,
)


class _CalendarClient:
    def __init__(self, commune: str):
        canonical = COMMUNES_NORMALIZED.get(_normalize_commune(commune))
        if canonical is None:
            raise SourceArgumentNotFoundWithSuggestions("commune", commune, COMMUNES)
        self.commune = canonical

    def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        panel_text = self._get_panel_text(soup, self.commune)
        if panel_text is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self.commune, COMMUNES
            )
        entries: list[dict] = []
        entries.extend(self._parse_ordures_menageres(panel_text))
        entries.extend(self._parse_emballages(panel_text))
        return entries

    @staticmethod
    def _get_panel_text(soup: BeautifulSoup, commune: str) -> str | None:
        """Find the accordion panel matching `commune` and return its plain text."""
        for heading in soup.select("h4.panel-title"):
            link = heading.find("a")
            if not link:
                continue
            name = link.get_text(strip=True)
            if _normalize_commune(name) != _normalize_commune(commune):
                continue
            href = link.get("href", "")
            if not isinstance(href, str) or not href.startswith("#"):
                continue
            panel = soup.find(id=href[1:])
            if panel is None:
                continue
            return panel.get_text("\n", strip=True)
        return None

    @staticmethod
    def _parse_ordures_menageres(text: str) -> list[dict]:
        """Parse the explicit "Calendrier/Collectes <year>" household-waste dates."""
        match = re.search(
            "(?:Calendrier|Collectes)\\s+(\\d{4})\\s*\\n(.*?)\\nEmballages\\s*:",
            text,
            re.DOTALL,
        )
        if not match:
            return []
        year = int(match.group(1))
        block = match.group(2)
        entries = []
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            low = _strip_accents(line).lower()
            month = None
            for mois_name, mois_num in MOIS_MAP.items():
                if re.search(f"\\b{mois_name}\\b", low):
                    month = mois_num
                    break
            if month is None:
                continue
            for day_match in re.finditer("(\\d{1,2})(?:er)?\\b", line):
                try:
                    collection_date = date(year, month, int(day_match.group(1)))
                except ValueError:
                    continue
                entries.append({"date": collection_date, "type": "Ordures ménagères"})
        return entries

    @staticmethod
    def _parse_emballages(text: str) -> list[dict]:
        """Parse the weekly recycling ("Emballages") collection, applying holiday shifts."""
        match = re.search("Emballages\\s*:\\s*\\n(.*?)\\nPapiers", text, re.DOTALL)
        if not match:
            return []
        block = match.group(1)
        if "conteneur" in block.lower():
            return []
        weekday_match = re.search(
            "chaque semaine le (\\w+)", _strip_accents(block).lower()
        )
        if not weekday_match:
            return []
        weekday = WEEKDAY_MAP.get(weekday_match.group(1))
        if weekday is None:
            return []
        today = date.today()
        occurrences = {
            dt.date()
            for dt in rrule(
                freq=WEEKLY,
                dtstart=today - timedelta(days=7),
                count=60,
                byweekday=weekday,
            )
        }
        for exc_match in EXCEPTION_PATTERN.finditer(block):
            orig_day, orig_month_str, orig_year, dest_day, dest_month_str, dest_year = (
                exc_match.groups()
            )
            orig_month = MOIS_MAP.get(_strip_accents(orig_month_str).lower())
            dest_month = MOIS_MAP.get(_strip_accents(dest_month_str).lower())
            if orig_month is None or dest_month is None:
                continue
            resolved_orig_year = int(orig_year) if orig_year else int(dest_year)
            try:
                orig_date = date(resolved_orig_year, orig_month, int(orig_day))
                dest_date = date(int(dest_year), dest_month, int(dest_day))
            except ValueError:
                continue
            occurrences.discard(orig_date)
            occurrences.add(dest_date)
        return [
            {"date": collection_date, "type": "Emballages"}
            for collection_date in sorted(occurrences)
        ]


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


def _request_params(commune: str, **_) -> None:
    _CalendarClient(commune)


calendar_retriever = Request(DATA_URL, params=_request_params, timeout=30)
