import re
from datetime import date, timedelta
from typing import ClassVar, final

import holidays
from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Demonstrates: a recurrence source whose holiday calendar comes from the
# holidays library (France, Alsace-Moselle subdivision "6AE") instead of
# hand-rolled easter arithmetic, and whose French weekday names resolve via the
# Babel-backed recurrence vocabulary. The provider-specific bits (the free-text
# "ferie" move/cancellation rules, the even/odd-week cadence) stay in the
# preprocess, which yields (date, label) rows for a standard ICSTransformer.

API_URL = (
    "https://data.mulhouse-alsace.fr/api/explore/v2.1/catalog/datasets/"
    "m2a_collecte-en-porte-a-porte-des-dechets-menagers_m2a/records"
)

# (frequency field, day field, label, waste type)
WASTE_FIELDS = (
    ("freq_omr", "jour_omr", "Ordures ménagères", GENERAL_WASTE),
    ("freq_recyc", "jour_recyc", "Tri sélectif", RECYCLABLES),
    ("freq_bio_d", "jour_bio", "Bio-déchets", FOOD_WASTE),
    ("freq_vert", "jour_vert", "Déchets verts", GARDEN_WASTE),
)
_TYPE_MAP = {label: waste_type for _f, _d, label, waste_type in WASTE_FIELDS}

HORIZON_WEEKS = 26

_DATE_TOKEN = r"(\d{1,2}/\d{1,2}/\d{2,4})"
_REPORT_RE = re.compile(
    rf"{_DATE_TOKEN}\s+report[ée]\s+(?:au|le)\s+{_DATE_TOKEN}", re.IGNORECASE
)
_NON_REPORTE_RE = re.compile(rf"{_DATE_TOKEN}\s+non\s+report[ée]", re.IGNORECASE)

# The ferie notes use either a 4- or 2-digit year; try both known formats.
_FR_DATE_FORMATS = (
    date_parsers.for_format("%d/%m/%Y"),
    date_parsers.for_format("%d/%m/%y"),
)


def _parse_french_date(value: str) -> date | None:
    for parse in _FR_DATE_FORMATS:
        try:
            return parse(value)
        except ValueError:
            continue
    return None


def _parse_ferie(
    ferie: str | None, span: tuple[date, date]
) -> tuple[dict[date, date], set[date]]:
    """Parse the provider's free-text holiday notes into moves + cancellations."""
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
        # Alsace-Moselle public holidays (subdiv "6AE" adds Good Friday + 26 Dec).
        fr_holidays = holidays.France(
            years=range(start.year, end.year + 1), subdiv="6AE"
        )
        for holiday in fr_holidays:
            if start <= holiday <= end and holiday not in moves:
                cancellations.add(holiday)

    return moves, cancellations


def _project_dates(jour: str, freq: str, start: date, weeks: int) -> list[date]:
    """Project a French weekday-plus-cadence string into concrete dates."""
    weekdays = [
        wd
        for token in re.split(r"\s+|,|;|\bet\b", jour.lower())
        if (wd := recurrence.weekday(token.strip())) is not None
    ]
    if not weekdays:
        return []

    dates: list[date] = []
    for wd in weekdays:
        first = recurrence.next_weekday(wd, on_or_after=start)
        dates.extend(recurrence.recurring(first, recurrence.WEEKLY, weeks))

    f = freq.lower()
    if "toutes les 2 semaines" in f:
        if "paire" in f and "impaire" not in f:
            return [d for d in dates if d.isocalendar().week % 2 == 0]
        if "impaire" in f:
            return [d for d in dates if d.isocalendar().week % 2 == 1]
    return sorted(dates)


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


@final
class Source(BaseSource):
    TITLE = "Mulhouse Alsace Agglomération (m2A)"
    DESCRIPTION = (
        "Source for door-to-door household waste collection in the Mulhouse "
        "Alsace Agglomération (m2A), based on its open data portal."
    )
    URL = "https://data.mulhouse-alsace.fr/"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Wittelsheim": {"commune": "Wittelsheim"},
        "Mulhouse - Centre Ville": {"commune": "Mulhouse", "quartier": "Centre Ville"},
        "Habsheim": {"commune": "Habsheim"},
    }

    # One structure, many communes: each is a Region (the same pipeline with a
    # different `commune`), surfaced as its own README / sources.json listing.
    REGIONS = (
        *(
            region(name, commune=name)
            for name in (
                "Bantzenheim",
                "Bruebach",
                "Feldkirch",
                "Flaxlanden",
                "Galfingue",
                "Habsheim",
                "Illzach",
                "Morschwiller-le-Bas",
                "Richwiller",
                "Rixheim",
                "Wittelsheim",
                "Zillisheim",
                "Zimmersheim",
                "Baldersheim",
                "Battenheim",
                "Bollwiller",
                "Eschentzwiller",
                "Heimsbrunn",
                "Hombourg",
                "Pfastatt",
                "Reiningue",
                "Riedisheim",
                "Sausheim",
                "Steinbrunn-le-Bas",
                "Ungersheim",
                "Wittenheim",
                "Berrwiller",
                "Brunstatt-Didenheim",
                "Chalampé",
                "Dietwiller",
                "Kingersheim",
                "Lutterbach",
                "Niffer",
                "Ottmarsheim",
                "Petit-Landau",
                "Pulversheim",
                "Ruelisheim",
                "Staffelfelden",
            )
        ),
        region("Mulhouse", commune="Mulhouse", quartier="Centre Ville"),
    )

    PARAMS = (
        text_field("commune", label="Municipality"),
        text_field("quartier", label="District", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "fr": "Indiquez votre commune; pour Mulhouse précisez aussi le quartier.",
        "en": "Provide your municipality; for Mulhouse also provide the district.",
    }

    retrieve = retrievers.HttpGetRetriever(
        url=API_URL,
        params=lambda commune, **_: {"where": f'com_nom="{commune}"', "limit": 100},
    )
    parse = parsers.JsonParser("results")
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, commune: str, quartier: str | None = None):
        super().__init__(commune=commune, quartier=quartier)

    def _list_communes(self, source) -> list[str]:
        resp = source.session.get(
            API_URL,
            params={"select": "com_nom", "limit": 100, "group_by": "com_nom"},
            timeout=30,
        )
        return sorted({r["com_nom"] for r in resp.json().get("results", [])})

    def _select_row(self, rows: list[dict]) -> dict:
        if len(rows) == 1:
            return rows[0]
        commune = self.params["commune"]
        quartier = self.params.get("quartier")
        quartiers = sorted({_clean(r.get("quartier")) for r in rows})
        if quartier is None:
            raise SourceArgumentRequiredWithSuggestions(
                "quartier",
                f"{commune} has multiple districts; please specify one.",
                quartiers,
            )
        for row in rows:
            if _clean(row.get("quartier")) == quartier:
                return row
        raise SourceArgumentNotFoundWithSuggestions("quartier", quartier, quartiers)

    def preprocess(self, records, source=None):
        if not records:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self.params["commune"], self._list_communes(source)
            )

        row = self._select_row(list(records))
        today = date.today()
        end = today + timedelta(weeks=HORIZON_WEEKS)
        moves, cancellations = _parse_ferie(row.get("ferie"), (today, end))

        for freq_field, jour_field, label, _waste_type in WASTE_FIELDS:
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
                # (date, label) row for the standard ICSTransformer.
                yield (effective, label)
