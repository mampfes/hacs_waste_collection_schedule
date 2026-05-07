import re
from datetime import date, datetime, timedelta

import requests
from dateutil.easter import easter
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Mulhouse Alsace Agglomération (m2A)"
DESCRIPTION = (
    "Source for door-to-door household waste collection in the Mulhouse "
    "Alsace Agglomération (m2A), based on its open data portal."
)
URL = "https://data.mulhouse-alsace.fr/"
COUNTRY = "fr"

API_URL = (
    "https://data.mulhouse-alsace.fr/api/explore/v2.1/catalog/datasets/"
    "m2a_collecte-en-porte-a-porte-des-dechets-menagers_m2a/records"
)

TEST_CASES = {
    "Wittelsheim": {"commune": "Wittelsheim"},
    "Mulhouse - Centre Ville": {"commune": "Mulhouse", "quartier": "Centre Ville"},
    "Habsheim": {"commune": "Habsheim"},
}

EXTRA_INFO = [
    {"title": "Bantzenheim", "default_params": {"commune": "Bantzenheim"}},
    {"title": "Bruebach", "default_params": {"commune": "Bruebach"}},
    {"title": "Feldkirch", "default_params": {"commune": "Feldkirch"}},
    {"title": "Flaxlanden", "default_params": {"commune": "Flaxlanden"}},
    {"title": "Galfingue", "default_params": {"commune": "Galfingue"}},
    {"title": "Habsheim", "default_params": {"commune": "Habsheim"}},
    {"title": "Illzach", "default_params": {"commune": "Illzach"}},
    {
        "title": "Morschwiller-le-Bas",
        "default_params": {"commune": "Morschwiller-le-Bas"},
    },
    {"title": "Richwiller", "default_params": {"commune": "Richwiller"}},
    {"title": "Rixheim", "default_params": {"commune": "Rixheim"}},
    {"title": "Wittelsheim", "default_params": {"commune": "Wittelsheim"}},
    {"title": "Zillisheim", "default_params": {"commune": "Zillisheim"}},
    {"title": "Zimmersheim", "default_params": {"commune": "Zimmersheim"}},
    {"title": "Baldersheim", "default_params": {"commune": "Baldersheim"}},
    {"title": "Battenheim", "default_params": {"commune": "Battenheim"}},
    {"title": "Bollwiller", "default_params": {"commune": "Bollwiller"}},
    {"title": "Eschentzwiller", "default_params": {"commune": "Eschentzwiller"}},
    {"title": "Heimsbrunn", "default_params": {"commune": "Heimsbrunn"}},
    {"title": "Hombourg", "default_params": {"commune": "Hombourg"}},
    {"title": "Pfastatt", "default_params": {"commune": "Pfastatt"}},
    {"title": "Reiningue", "default_params": {"commune": "Reiningue"}},
    {"title": "Riedisheim", "default_params": {"commune": "Riedisheim"}},
    {"title": "Sausheim", "default_params": {"commune": "Sausheim"}},
    {
        "title": "Steinbrunn-le-Bas",
        "default_params": {"commune": "Steinbrunn-le-Bas"},
    },
    {"title": "Ungersheim", "default_params": {"commune": "Ungersheim"}},
    {"title": "Wittenheim", "default_params": {"commune": "Wittenheim"}},
    {"title": "Berrwiller", "default_params": {"commune": "Berrwiller"}},
    {
        "title": "Brunstatt-Didenheim",
        "default_params": {"commune": "Brunstatt-Didenheim"},
    },
    {"title": "Chalampé", "default_params": {"commune": "Chalampé"}},
    {"title": "Dietwiller", "default_params": {"commune": "Dietwiller"}},
    {"title": "Kingersheim", "default_params": {"commune": "Kingersheim"}},
    {"title": "Lutterbach", "default_params": {"commune": "Lutterbach"}},
    {"title": "Niffer", "default_params": {"commune": "Niffer"}},
    {"title": "Ottmarsheim", "default_params": {"commune": "Ottmarsheim"}},
    {"title": "Petit-Landau", "default_params": {"commune": "Petit-Landau"}},
    {"title": "Pulversheim", "default_params": {"commune": "Pulversheim"}},
    {"title": "Ruelisheim", "default_params": {"commune": "Ruelisheim"}},
    {"title": "Staffelfelden", "default_params": {"commune": "Staffelfelden"}},
    {
        "title": "Mulhouse",
        "default_params": {"commune": "Mulhouse", "quartier": "Centre Ville"},
    },
]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "fr": (
        "Indiquez le nom de votre commune au sein de Mulhouse Alsace "
        "Agglomération (par exemple « Wittelsheim »). Pour Mulhouse, "
        "précisez aussi le quartier (par exemple « Rebberg », "
        "« Centre Ville »)."
    ),
    "en": (
        "Provide the name of your municipality within Mulhouse Alsace "
        'Agglomération (e.g. "Wittelsheim"). For Mulhouse, also provide '
        'the district name (e.g. "Rebberg", "Centre Ville").'
    ),
}

PARAM_DESCRIPTIONS = {
    "fr": {
        "commune": "Nom de la commune",
        "quartier": "Quartier (uniquement pour Mulhouse)",
    },
    "en": {
        "commune": "Municipality name",
        "quartier": "District (only for Mulhouse)",
    },
}

PARAM_TRANSLATIONS = {
    "fr": {"commune": "Commune", "quartier": "Quartier"},
    "en": {"commune": "Municipality", "quartier": "District"},
}


WASTE_FIELDS = (
    # (frequency field, day field, label, icon)
    ("freq_omr", "jour_omr", "Ordures ménagères", "mdi:trash-can"),
    ("freq_recyc", "jour_recyc", "Tri sélectif", "mdi:recycle"),
    ("freq_bio_d", "jour_bio", "Bio-déchets", "mdi:leaf-circle"),
    ("freq_vert", "jour_vert", "Déchets verts", "mdi:leaf"),
)

FR_WEEKDAYS = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}

HORIZON_WEEKS = 26

_DATE_TOKEN = r"(\d{1,2}/\d{1,2}/\d{2,4})"
_REPORT_RE = re.compile(
    rf"{_DATE_TOKEN}\s+report[ée]\s+(?:au|le)\s+{_DATE_TOKEN}", re.IGNORECASE
)
_NON_REPORTE_RE = re.compile(rf"{_DATE_TOKEN}\s+non\s+report[ée]", re.IGNORECASE)


def _parse_french_date(value: str) -> date | None:
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _french_holidays(year: int) -> set[date]:
    e = easter(year)
    return {
        date(year, 1, 1),
        e - timedelta(days=2),  # Vendredi saint (Alsace-Moselle)
        e + timedelta(days=1),  # Lundi de Pâques
        date(year, 5, 1),
        date(year, 5, 8),
        e + timedelta(days=39),  # Ascension
        e + timedelta(days=50),  # Lundi de Pentecôte
        date(year, 7, 14),
        date(year, 8, 15),
        date(year, 11, 1),
        date(year, 11, 11),
        date(year, 12, 25),
        date(year, 12, 26),  # Saint-Étienne (Alsace-Moselle)
    }


def _parse_ferie(
    ferie: str | None, span: tuple[date, date]
) -> tuple[dict[date, date], set[date]]:
    moves: dict[date, date] = {}
    cancellations: set[date] = set()
    if not ferie:
        return moves, cancellations

    for match in _REPORT_RE.finditer(ferie):
        src = _parse_french_date(match.group(1))
        dst = _parse_french_date(match.group(2))
        if src and dst:
            moves[src] = dst

    for match in _NON_REPORTE_RE.finditer(ferie):
        cancelled = _parse_french_date(match.group(1))
        if cancelled:
            cancellations.add(cancelled)

    if "ne sont pas maintenues" in ferie.lower():
        start, end = span
        for year in range(start.year, end.year + 1):
            for holiday in _french_holidays(year):
                if start <= holiday <= end and holiday not in moves:
                    cancellations.add(holiday)

    return moves, cancellations


def _parse_weekdays(jour: str):
    weekdays = []
    for token in re.split(r"\s+|,|;|\bet\b", jour.lower()):
        token = token.strip()
        if token in FR_WEEKDAYS:
            weekdays.append(FR_WEEKDAYS[token])
    return weekdays


def _project_dates(jour: str, freq: str, start: date, weeks: int) -> list[date]:
    weekdays = _parse_weekdays(jour)
    if not weekdays:
        return []

    occurrences = [
        dt.date()
        for dt in rrule(
            freq=WEEKLY,
            dtstart=start,
            count=weeks * len(weekdays),
            byweekday=weekdays,
        )
    ]

    f = freq.lower()
    if "toutes les 2 semaines" in f:
        if "paire" in f and "impaire" not in f:
            return [d for d in occurrences if d.isocalendar().week % 2 == 0]
        if "impaire" in f:
            return [d for d in occurrences if d.isocalendar().week % 2 == 1]

    return occurrences


class Source:
    def __init__(self, commune: str, quartier: str | None = None):
        self._commune = commune
        self._quartier = quartier

    def _list_communes(self) -> list[str]:
        params = {"select": "com_nom", "limit": 100, "group_by": "com_nom"}
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        return sorted({row["com_nom"] for row in response.json().get("results", [])})

    def _fetch_rows(self) -> list[dict]:
        params = {
            "where": f'com_nom="{self._commune}"',
            "limit": 100,
        }
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def _select_row(self, rows: list[dict]) -> dict:
        if len(rows) == 1:
            return rows[0]

        quartiers = sorted({row["quartier"] for row in rows})
        if self._quartier is None:
            raise SourceArgumentRequiredWithSuggestions(
                "quartier",
                f"{self._commune} has multiple districts; please specify one.",
                quartiers,
            )

        for row in rows:
            if row["quartier"] == self._quartier:
                return row

        raise SourceArgumentNotFoundWithSuggestions(
            "quartier", self._quartier, quartiers
        )

    def fetch(self) -> list[Collection]:
        rows = self._fetch_rows()
        if not rows:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, self._list_communes()
            )

        row = self._select_row(rows)

        today = date.today()
        end = today + timedelta(weeks=HORIZON_WEEKS)
        moves, cancellations = _parse_ferie(row.get("ferie"), (today, end))

        entries: list[Collection] = []
        for freq_field, jour_field, label, icon in WASTE_FIELDS:
            jour = row.get(jour_field)
            freq = row.get(freq_field)
            if not jour or not freq:
                continue

            for collection_date in _project_dates(jour, freq, today, HORIZON_WEEKS):
                if collection_date in cancellations:
                    continue
                effective = moves.get(collection_date, collection_date)
                if effective in cancellations:
                    continue
                entries.append(Collection(date=effective, t=label, icon=icon))

        return entries
