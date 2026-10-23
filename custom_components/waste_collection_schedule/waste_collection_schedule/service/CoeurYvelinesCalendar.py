"""CoeurYvelinesCalendar retrieval and parsing, using the pipeline HTTP session."""

import re
import unicodedata
from datetime import date
from typing import Any

from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, MONTHLY, SA, SU, TH, TU, WE, WEEKLY, rrule

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

DATA_URL = (
    "https://www.coeur-yvelines.fr/environnement/calendriers-de-collecte-des-dechets/"
)
COMMUNES = {
    "Auteuil-le-Roi": 2,
    "Autouillet": 3,
    "Bazoches-sur-Guyonne": 4,
    "Behoust": 5,
    "Beynes": 1,
    "Boissy-sans-Avoir": 6,
    "Flexanville": 7,
    "Galluis": 8,
    "Gambais": 9,
    "Garancières": 10,
    "Goupillières": 11,
    "Grosrouvre": 12,
    "Jouars-Pontchartrain": 13,
    "La Queue-lez-Yvelines": 14,
    "Le Tremblay-sur-Mauldre": 15,
    "Les Mesnuls": 16,
    "Marcq": 17,
    "Mareil-le-Guyon": 18,
    "Méré": 19,
    "Millemont": 20,
    "Montfort-l'Amaury": 21,
    "Neauphle-le-Château": 22,
    "Neauphle-le-Vieux": 23,
    "Saint-Germain-de-la-Grange": 24,
    "Saint-Rémy-l'Honoré": 25,
    "Saulx-Marchais": 26,
    "Thiverval-Grignon": 27,
    "Thoiry": 28,
    "Vicq": 29,
    "Villiers-le-Mahieu": 30,
    "Villiers-Saint-Frédéric": 31,
}


def _normalize(s: str) -> str:
    """Remove accents, lower-case, and collapse separators for fuzzy matching."""
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub("[-'‘’]", " ", s.lower())
    return re.sub("\\s+", " ", s).strip()


COMMUNES_NORMALIZED = {_normalize(c): c for c in COMMUNES}

WEEKDAY_MAP = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}
WEEKDAY_ORDER = [MO, TU, WE, TH, FR, SA, SU]
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


class _CalendarClient:
    def __init__(self, commune: str):
        normalized = _normalize(commune)
        canonical = COMMUNES_NORMALIZED.get(normalized)
        if canonical is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", commune, list(COMMUNES)
            )
        self.commune = canonical
        self._commune_id = COMMUNES[canonical]

    def parse(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        year = date.today().year
        heading = soup.find("h2", string=re.compile("Calendrier\\s+\\d{4}"))
        if heading:
            m = re.search("\\d{4}", heading.get_text())
            if m:
                year = int(m.group())
        entries: list[dict] = []
        for block in soup.select("div.semaine"):
            title_tag = block.find("h3")
            periode_tag = block.find("p", class_="periode")  # codespell:ignore periode
            jours_div = block.find("div", class_="jours")
            if not title_tag or not periode_tag or (not jours_div):
                continue
            bin_type = title_tag.get_text(strip=True)
            periode_text = periode_tag.get_text(strip=True)
            spans = jours_div.find_all("span")
            checked_weekdays = [
                WEEKDAY_ORDER[i]
                for i, span in enumerate(spans)
                if "checked" in (span.get("class") or []) and i < len(WEEKDAY_ORDER)
            ]
            for collection_date in self._dates_for_period(
                periode_text, year, checked_weekdays
            ):
                entries.append({"date": collection_date, "type": bin_type})
        return entries

    @staticmethod
    def _dates_for_period(
        periode_text: str, year: int, checked_weekdays: list
    ) -> list[date]:
        normalized = _normalize(periode_text)
        if "rendez vous" in normalized:
            return []
        if not checked_weekdays:
            return []
        if "derniers" in normalized and "mois pairs" in normalized:
            matched_weekday = None
            for name, weekday_obj in WEEKDAY_MAP.items():
                if name in normalized:
                    matched_weekday = weekday_obj
                    break
            if matched_weekday is None:
                matched_weekday = checked_weekdays[0]
            dates: list[date] = []
            for month in (2, 4, 6, 8, 10, 12):
                if month == 12:
                    month_end = date(year, 12, 31)
                else:
                    month_end = date(year, month + 1, 1)
                dates.extend(
                    dt.date()
                    for dt in rrule(
                        freq=MONTHLY,
                        dtstart=date(year, month, 1),
                        until=month_end,
                        byweekday=matched_weekday,
                        bysetpos=-1,
                        count=1,
                    )
                )
            return dates
        range_match = re.search(
            "du\\s+(\\d{1,2})(?:er)?\\s+([a-zàâäéèêëïîôùûüç]+)\\s+au\\s+(\\d{1,2})(?:er)?\\s+([a-zàâäéèêëïîôùûüç]+)",
            periode_text.lower(),
        )
        if range_match:
            start_day, start_month_str, end_day, end_month_str = range_match.groups()
            start_month = MOIS_MAP.get(_normalize(start_month_str))
            end_month = MOIS_MAP.get(_normalize(end_month_str))
            if start_month and end_month:
                try:
                    start_date = date(year, start_month, int(start_day))
                    end_date = date(year, end_month, int(end_day))
                except ValueError:
                    return []
                return [
                    dt.date()
                    for dt in rrule(
                        freq=WEEKLY,
                        dtstart=start_date,
                        until=end_date,
                        byweekday=checked_weekdays,
                    )
                ]
        if re.search("\\d", periode_text):
            dates = []
            for m in re.finditer(
                "(\\d{1,2})(?:er)?\\s+([a-zàâäéèêëïîôùûüç]+)", periode_text.lower()
            ):
                collection_month = MOIS_MAP.get(_normalize(m.group(2)))
                if collection_month:
                    try:
                        dates.append(date(year, collection_month, int(m.group(1))))
                    except ValueError:
                        pass
            return dates
        return [
            dt.date()
            for dt in rrule(
                freq=WEEKLY,
                dtstart=date(year, 1, 1),
                until=date(year, 12, 31),
                byweekday=checked_weekdays,
            )
        ]


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


def _request_params(commune: str, **_) -> dict:
    return {"commune": _CalendarClient(commune)._commune_id}


calendar_retriever = Request(DATA_URL, params=_request_params)
