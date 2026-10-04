"""Chartres Métropole waste collection source.

The provider publishes one page per commune under
https://www.chartres-metropole.fr/collectes-par-commune/<slug>-collecte. Its
printed PDF calendars are image-only (no text layer), so the schedule is derived
from the machine-readable rules in the "Jours de collecte" section:

* ordinary household waste (``Ordures ménagères``) - one or two weekdays per
  week, optionally split into a ``secteur bacs`` and a ``secteur sacs``;
* packaging (``Emballages ménagers et papiers``) - one weekday, either every
  week or only on even/odd ISO weeks (``semaine paire`` / ``semaine impaire``);
* garden waste (``Déchets végétaux``) - one weekday, April to the end of
  November;
* bulky waste (``Encombrants``) - either the "Nth weekday of even months" rule
  or the explicit dates listed on the page.

The one documented exception is the bank-holiday rule: within a given week,
regular collections falling on or after a public holiday are postponed by one
day. Bulky waste is not shifted. The whole pipeline is shared components; the
provider-specific parts are the paragraph reader and the holiday adjustment.
"""

import re
import unicodedata
from datetime import date, timedelta
from typing import Any, ClassVar, final

import holidays
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    RequireRecords,
    Schedule,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

BASE_URL = "https://www.chartres-metropole.fr"
PAGE_TEMPLATE = BASE_URL + "/collectes-par-commune/{slug}-collecte"

# Number of weeks of recurring collections to project.
HORIZON_WEEKS = 26

GENERAL_KEY = "Ordures ménagères"
PACKAGING_KEY = "Emballages ménagers et papiers"
GARDEN_KEY = "Déchets végétaux"
BULKY_KEY = "Encombrants"

# Commune name (as shown by the provider) -> page slug in the annuaire.
COMMUNES: dict[str, str] = {
    "Allones": "allones",
    "Amilly": "amilly",
    "Bailleau-L’Évêque": "bailleau-leveque",
    "Barjouville": "barjouville",
    "Berchères-les-Pierres": "bercheres-les-pierres",
    "Berchères-Saint-Germain": "bercheres-saint-germain",
    "Boisville-la-Saint-Père": "boisville-la-saint-pere",
    "Boncé": "bonce",
    "Bouglainval": "bouglainval",
    "Briconville": "briconville",
    "Challet": "challet",
    "Champhol": "champhol",
    "Champseru": "champseru",
    "Chartainvilliers": "chartainvilliers",
    "Chartres": "chartres",
    "Chartres - Plateau de Rechèvres": "chartres-plateau-de-rechevres",
    "Chartres hypercentre et basse-ville": "chartres-hypercentre-et-basse-ville",
    "Chauffours": "chauffours",
    "Cintray": "cintray",
    "Clévilliers": "clevilliers",
    "Coltainville": "coltainville",
    "Corancez": "corancez",
    "Dammarie et Bois-de-Mivoye": "dammarie-et-bois-de-mivoye",
    "Dangers": "dangers",
    "Denonville": "denonville",
    "Ermenonville-la-Grande": "ermenonville-la-grande",
    "Fontenay-sur-Eure": "fontenay-sur-eure",
    "Francourville": "francourville",
    "Fresnay-le-Comte": "fresnay-le-comte",
    "Fresnay-le-Gilmert": "fresnay-le-gilmert",
    "Gasville-Oisème": "gasville-oiseme",
    "Gellainville": "gellainville",
    "Houville-la-Branche": "houville-la-branche",
    "Houx": "houx",
    "Jouy": "jouy",
    "La Bourdinière-Saint-Loup": "la-bourdiniere-saint-loup",
    "Le Coudray": "le-coudray",
    "Lèves": "leves",
    "Lucé": "luce",
    "Luisant": "luisant",
    "Maintenon": "maintenon",
    "Mainvilliers": "mainvilliers",
    "Meslay-le-Grenet": "meslay-le-grenet",
    "Meslay-le-Vidame": "meslay-le-vidame",
    "Mignières": "mignieres",
    "Mittainvilliers-Vérigny": "mittainvilliers-verigny",
    "Moinville-la-Jeulin": "moinville-la-jeulin",
    "Morancez": "morancez",
    "Nogent-le-Phaye": "nogent-le-phaye",
    "Nogent-sur-Eure": "nogent-sur-eure",
    "Oinville-sous-Auneau": "oinville-sous-auneau",
    "Ollé": "olle",
    "Poisvilliers": "poisvilliers",
    "Prunay-le-Gillon": "prunay-le-gillon",
    "Roinville-sous-Auneau": "roinville-sous-auneau",
    "Saint-Aubin-des-Bois": "saint-aubin-des-bois",
    "Saint-Georges-sur-Eure": "saint-georges-sur-eure",
    "Saint-Léger-des-Aubées": "saint-leger-des-aubees",
    "Saint-Prest": "saint-prest",
    "Sandarville": "sandarville",
    "Santeuil": "santeuil",
    "Sours": "sours",
    "Theuville": "theuville",
    "Thivars": "thivars",
    "Umpeau": "umpeau",
    "Ver-lès-Chartres": "ver-les-chartres",
    "Vitray-en-Beauce": "vitray-en-beauce",
    "Voise": "voise",
}

_TYPE_MAP = {
    GENERAL_KEY: wt.GENERAL_WASTE,
    f"{GENERAL_KEY} (bacs)": wt.GENERAL_WASTE,
    f"{GENERAL_KEY} (sacs)": wt.GENERAL_WASTE,
    PACKAGING_KEY: wt.RECYCLABLES,
    GARDEN_KEY: wt.GARDEN_WASTE,
    BULKY_KEY: wt.BULKY_WASTE,
}

_SECTEUR_ALIASES = {"bacs": "bacs", "bac": "bacs", "sacs": "sacs", "sac": "sacs"}

# Months in which garden waste is collected ("d'avril à fin novembre").
_GARDEN_START_MONTH = 4
_GARDEN_END_MONTH = 11

_ENCOMBRANTS_RULE_RE = re.compile(
    r"(\d+)(?:er|eme|e)?\s+"
    r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)"
    r"\s+des\s+mois\s+pairs"
)

_EXPLICIT_DATE_RE = re.compile(rf"(\d{{1,2}})\s+({'|'.join(recurrence.MONTHS)})")


def _normalize(value: str) -> str:
    """Lowercase, strip accents and turn separators into single spaces."""
    value = "".join(
        c
        for c in unicodedata.normalize("NFD", value.lower())
        if unicodedata.category(c) != "Mn"
    )
    for separator in ("’", "'", "-", "–"):
        value = value.replace(separator, " ")
    return re.sub(r"\s+", " ", value).strip()


_SLUG_BY_COMMUNE = {_normalize(name): slug for name, slug in COMMUNES.items()}


def _coerce_secteur(value: Any) -> str:
    """Normalise the optional ``secteur`` value, rejecting anything else."""
    key = _normalize(str(value))
    if key not in _SECTEUR_ALIASES:
        raise SourceArgumentNotFoundWithSuggestions("secteur", value, ["bacs", "sacs"])
    return _SECTEUR_ALIASES[key]


def _weekdays(normalized_body: str) -> list[int]:
    """The weekdays named in a French "mardi et vendredi" style field."""
    result: list[int] = []
    for token in re.split(r"\s+|,|;|\bet\b", normalized_body):
        weekday = recurrence.weekday(token.strip())
        if weekday is not None and weekday not in result:
            result.append(weekday)
    return result


def _encombrants_rule(normalized_text: str) -> tuple[int, int] | None:
    """Parse e.g. '2eme jeudi des mois pairs' into (2, Thursday)."""
    match = _ENCOMBRANTS_RULE_RE.search(normalized_text)
    if not match:
        return None
    return int(match.group(1)), recurrence.WEEKDAYS[match.group(2)]


def _infer_year(month: int, day: int, today: date) -> int:
    for year in (today.year, today.year + 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if candidate >= today - timedelta(days=31):
            return year
    return today.year + 1


def _explicit_dates(normalized_body: str, today: date) -> list[date]:
    """Parse a list like 'mardi 27 janvier et jeudi 9 juillet 2026'."""
    year_match = re.search(r"\b(20\d{2})\b", normalized_body)
    year = int(year_match.group(1)) if year_match else None
    result = []
    for match in _EXPLICIT_DATE_RE.finditer(normalized_body):
        day = int(match.group(1))
        month = recurrence.MONTHS[match.group(2)]
        chosen_year = year if year else _infer_year(month, day, today)
        try:
            result.append(date(chosen_year, month, day))
        except ValueError:
            continue
    return result


def _describe(tag: Any, source: Any = None) -> Any:
    """Yield one Schedule per collection rule found in a description paragraph."""
    text = tag.get_text(" ", strip=True).replace("\xa0", " ")
    normalized = _normalize(text)
    label, separator, body = text.partition(":")
    normalized_label = _normalize(label)
    normalized_body = _normalize(body) if separator else normalized
    today = date.today()
    horizon = today + timedelta(weeks=HORIZON_WEEKS)
    secteur = source.params.get("secteur") if source is not None else None

    if normalized.startswith("ordures menageres"):
        if "depot en conteneur" in normalized:
            return
        if "secteur bacs" in normalized_label:
            if secteur not in (None, "bacs"):
                return
            key = f"{GENERAL_KEY} (bacs)"
        elif "secteur sacs" in normalized_label:
            if secteur not in (None, "sacs"):
                return
            key = f"{GENERAL_KEY} (sacs)"
        else:
            key = GENERAL_KEY
        for weekday in _weekdays(normalized_body):
            yield Schedule(
                key,
                recurrence.next_weekday(weekday, on_or_after=today),
                count=HORIZON_WEEKS,
            )

    elif normalized.startswith("emballages menagers et papiers"):
        parity: str | None = None
        if "semaine impaire" in normalized:
            parity = "odd"
        elif "semaine paire" in normalized:
            parity = "even"
        for weekday in _weekdays(normalized_body):
            yield Schedule(
                PACKAGING_KEY,
                recurrence.next_weekday(weekday, on_or_after=today),
                count=HORIZON_WEEKS,
                iso_week_parity=parity,
            )

    elif normalized.startswith("dechets vegetaux"):
        if "point d apport" in normalized:
            return
        weekdays = _weekdays(normalized_body)
        if not weekdays:
            return
        for year in (today.year, today.year + 1):
            not_before = max(today, date(year, _GARDEN_START_MONTH, 1))
            # "d'avril à fin novembre" - until the last day of November.
            until = min(
                date(year, _GARDEN_END_MONTH + 1, 1) - timedelta(days=1), horizon
            )
            if not_before > until:
                continue
            for weekday in weekdays:
                yield Schedule(
                    GARDEN_KEY,
                    recurrence.next_weekday(weekday, on_or_after=not_before),
                    not_before=not_before,
                    until=until,
                )

    elif normalized.startswith("encombrants"):
        extra: set[date] = set()
        rule = _encombrants_rule(normalized)
        if rule is not None:
            occurrence, weekday = rule
            for candidate in recurrence.monthly_nth_weekdays(
                weekday, occurrence, 13, on_or_after=today
            ):
                if candidate.month % 2 == 0 and candidate <= horizon:
                    extra.add(candidate)
        for candidate in _explicit_dates(normalized_body, today):
            if today <= candidate <= horizon:
                extra.add(candidate)
        if extra:
            # An explicit date list with no cadence of its own.
            yield Schedule(
                BULKY_KEY,
                today,
                count=0,
                extra=tuple(sorted(extra)),
            )


def _france_holidays(source: Any, year: int) -> Any:
    cached = getattr(source, "_chartres_holidays", None)
    if cached is None:
        cached = holidays.France(years=range(year - 1, year + 2))
        source._chartres_holidays = cached
    return cached


def _adjust(collection_date: date, key: str, source: Any = None) -> date | None:
    """Postpone a regular collection that follows a holiday in the same week."""
    if key == BULKY_KEY:
        return collection_date
    fr_holidays = _france_holidays(source, collection_date.year)
    monday = collection_date - timedelta(days=collection_date.weekday())
    for offset in range(7):
        candidate = monday + timedelta(days=offset)
        if candidate > collection_date:
            break
        if candidate in fr_holidays:
            return collection_date + timedelta(days=1)
    return collection_date


def _page_url(commune: str) -> str:
    slug = _SLUG_BY_COMMUNE.get(_normalize(commune))
    if slug is None:
        raise SourceArgumentNotFoundWithSuggestions("commune", commune, list(COMMUNES))
    return PAGE_TEMPLATE.format(slug=slug)


@final
class Source(BaseSource):
    TITLE = "Chartres Métropole"
    DESCRIPTION = "Source for Chartres Métropole, France."
    URL = "https://www.chartres-metropole.fr/dechets/collectes"
    COUNTRY = "fr"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@kamaradclimber"]
    RAISE_ON_EMPTY = True
    # The bin and bag rounds are the same General Waste stream and can run on
    # the same weekday, so they collapse to identical entries once canonicalised.
    IGNORE_DUPLICATES_DEFAULT = True

    TEST_CASES: ClassVar[dict] = {
        "Lèves": {"commune": "Lèves"},
        "Lèves - secteur sacs": {"commune": "Lèves", "secteur": "sacs"},
        "Allones": {"commune": "Allones"},
        "Barjouville": {"commune": "Barjouville"},
        "Chartres": {"commune": "Chartres"},
        "Champhol": {"commune": "Champhol"},
    }

    # One structure, many communes: each is a Region (the same pipeline applied
    # to a different `commune`), surfaced as its own README / sources.json entry.
    REGIONS = tuple(region(name, commune=name) for name in COMMUNES)

    PARAMS = (
        municipality(field="commune"),
        text_field(
            "secteur", "Collection sector", optional=True, coerce=_coerce_secteur
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.chartres-metropole.fr/dechets/collectes, find your "
            "commune and use the name as displayed there. Set 'secteur' only if "
            "you know you are on the bin ('bacs') or bag ('sacs') round; leave it "
            "empty to receive both."
        ),
        "fr": (
            "Rendez-vous sur https://www.chartres-metropole.fr/dechets/collectes, "
            "recherchez votre commune et utilisez le nom affiché. Renseignez "
            "'secteur' uniquement si vous savez relever du secteur bacs ou sacs ; "
            "laissez vide pour recevoir les deux."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    retrieve = retrievers.HttpGetRetriever(
        url=lambda commune, **_: _page_url(commune),
    )
    # Each paragraph of the "Jours de collecte" block is one waste-type rule.
    parse = parsers.HtmlParser(".fiche-description p", require=[".fiche-description"])
    preprocess = Compose(
        RequireRecords(argument="commune"),
        RecurrenceExpander(_describe),
        HolidayShift(_adjust),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
