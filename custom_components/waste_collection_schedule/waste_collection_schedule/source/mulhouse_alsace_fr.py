import re
from datetime import date, timedelta
from typing import Any, ClassVar, Literal, final

import holidays
from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    Disambiguate,
    HolidayShift,
    RecurrenceExpander,
    RequireRecords,
    Schedule,
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
# Babel-backed recurrence vocabulary. The whole pipeline is shared components:
# the commune lookup guard, the district disambiguation, the cadence expansion
# and the holiday shift. The provider-specific bits (reading the free-text
# "ferie" rules and the even/odd-week wording) are the two callables below.

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


def _weekdays(jour: str) -> list[int]:
    """The weekdays named in a French "Mardi Jeudi et Samedi" style field."""
    return [
        wd
        for token in re.split(r"\s+|,|;|\bet\b", jour.lower())
        if (wd := recurrence.weekday(token.strip())) is not None
    ]


def _parity(freq: str) -> "Literal['even', 'odd'] | None":
    """The ISO-week parity a "toutes les 2 semaines" cadence runs on, if stated."""
    f = freq.lower()
    if "toutes les 2 semaines" in f:
        if "paire" in f and "impaire" not in f:
            return "even"
        if "impaire" in f:
            return "odd"
    return None


def _list_communes(source: Any) -> list[str]:
    """Every commune the dataset covers; the suggestions for an unknown one."""
    resp = source.session.get(
        API_URL,
        params={"select": "com_nom", "limit": 100, "group_by": "com_nom"},
        timeout=30,
    )
    return sorted({r["com_nom"] for r in resp.json().get("results", [])})


def _describe(row: dict, source: Any = None):
    """One Schedule per weekday of each round this district is served by."""
    today = date.today()
    end = today + timedelta(weeks=HORIZON_WEEKS)
    # Read once here, applied per collection by _adjust below.
    source.ferie = _parse_ferie(row.get("ferie"), (today, end))

    for freq_field, jour_field, label, _waste_type in WASTE_FIELDS:
        jour = row.get(jour_field)
        freq = row.get(freq_field)
        if not jour or not freq:
            continue
        parity = _parity(freq)
        for wd in _weekdays(jour):
            yield Schedule(
                label,
                recurrence.next_weekday(wd, on_or_after=today),
                recurrence.WEEKLY,
                HORIZON_WEEKS,
                iso_week_parity=parity,
            )


def _adjust(collection_date: date, key: str, source: Any = None) -> "date | None":
    """Apply the district's holiday notes: move a collection, or cancel it."""
    moves, cancellations = getattr(source, "ferie", ({}, set()))
    if collection_date in cancellations:
        return None
    effective = moves.get(collection_date, collection_date)
    return None if effective in cancellations else effective


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
    # One record per district of the commune, so: reject a commune the dataset
    # does not cover, narrow to the district asked for, expand its cadences,
    # then apply that district's own holiday notes.
    preprocess = Compose(
        RequireRecords(argument="commune", suggestions=_list_communes),
        Disambiguate(
            argument="quartier",
            key=lambda row: row.get("quartier"),
            reason="{commune} has multiple districts; please specify one.",
        ),
        RecurrenceExpander(_describe),
        HolidayShift(_adjust),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
