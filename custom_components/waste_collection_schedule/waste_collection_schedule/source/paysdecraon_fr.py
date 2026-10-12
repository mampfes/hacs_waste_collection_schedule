"""Waste collection schedules for the Communauté de Communes du Pays de Craon.

The Pays de Craon only publishes a yearly PDF that colours whole weeks as
household-waste or packaging weeks (public-holiday weeks are marked and push the
collection back one day). The bins are collected on the household's usual
weekday, which the user supplies; branch shredding ("broyage de branches") is
listed per municipality in the same PDF.
"""

import datetime
import re
from collections import Counter
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import lookups, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ColourCellCalendar import (
    GENERAL,
    HOLIDAY,
    PACKAGING,
    SPECIAL,
    CalendarDay,
    ColourCellCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_MEDIA_API_URL = "https://www.paysdecraon.fr/wp-json/wp/v2/media"
_PDF_NAME_RE = re.compile(r"calendrier-collecte-(\d{4})[^/]*\.pdf$", re.IGNORECASE)

_WEEKDAYS = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
}

_TYPE_MAP = {
    GENERAL: wt.GENERAL_WASTE,
    PACKAGING: wt.RECYCLABLES,
    SPECIAL: wt.GARDEN_WASTE,
}


def _commune_key(name: str) -> str:
    text = lookups.normalize_loose(name)
    text = re.sub(r"\bsaint\b", "st", text)
    return re.sub(r"\bsainte\b", "ste", text)


def _pdf_urls(response, *_, **__) -> list[str]:
    """The calendar PDF of every year from the current one on, oldest first."""
    latest: dict[int, tuple[str, str]] = {}
    for item in response.json():
        url = item.get("source_url") or ""
        match = _PDF_NAME_RE.search(url)
        if not match:
            continue
        year = int(match.group(1))
        published = item.get("date") or ""
        if year not in latest or published > latest[year][0]:
            latest[year] = (published, url)
    if not latest:
        raise ValueError(
            "no collection calendar PDF found, the media library may have changed"
        )
    this_year = datetime.date.today().year
    years = [y for y in latest if y >= this_year] or [max(latest)]
    return [latest[y][1] for y in sorted(years)]


def _collections(
    records: list[CalendarDay], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Project the painted weeks onto the household's weekday (and commune)."""
    assert source is not None
    weekday = _WEEKDAYS[lookups.normalize_loose(source.params["weekday"])]
    commune = source.params.get("commune")

    # later calendars override earlier ones for overlapping dates
    categories = {day.date: day.category for day in records}
    shredding: dict[datetime.date, list[str]] = {}
    for day in records:
        if day.category == SPECIAL and day.extra:
            shredding.setdefault(day.date, []).append(day.extra)

    weeks: dict[datetime.date, set[int]] = {}
    for date, category in categories.items():
        holidays = weeks.setdefault(
            date - datetime.timedelta(days=date.weekday()), set()
        )
        if category == HOLIDAY:
            holidays.add(date.weekday())

    for monday, holidays in sorted(weeks.items()):
        # after a public holiday the collection is postponed by one day
        shift = 1 if any(h <= weekday for h in holidays) else 0
        date = monday + datetime.timedelta(days=weekday + shift)
        category = categories.get(date)
        if category == SPECIAL:
            # branch shredding day: use the type of the rest of the week
            week = Counter(
                categories.get(monday + datetime.timedelta(days=i)) for i in range(6)
            )
            category = next(
                (c for c, _ in week.most_common() if c in (GENERAL, PACKAGING)), None
            )
        if category in (GENERAL, PACKAGING):
            yield date, category

    if commune:
        wanted = _commune_key(commune)
        known = {name for names in shredding.values() for name in names}
        if wanted not in {_commune_key(n) for n in known}:
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", commune, sorted(known)
            )
        for date, names in sorted(shredding.items()):
            if any(_commune_key(n) == wanted for n in names):
                yield date, SPECIAL


@final
class Source(BaseSource):
    TITLE = "Communauté de Communes du Pays de Craon"
    DESCRIPTION = (
        "Source for the Communauté de Communes du Pays de Craon (Mayenne), France."
    )
    URL = "https://www.paysdecraon.fr"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@Adin112"]

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Saint-Michel-de-la-Roë (mercredi)": {
            "weekday": "mercredi",
            "commune": "Saint-Michel-de-la-Roë",
        },
        "Renazé (lundi)": {"weekday": "lundi", "commune": "Renazé"},
        "No commune (vendredi)": {"weekday": "vendredi"},
    }

    PARAMS = (
        dropdown("weekday", list(_WEEKDAYS), label="Collection weekday"),
        municipality("commune", optional=True),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "The Pays de Craon calendar only shows whether a week is a household "
            "waste or a packaging week. Choose the weekday on which your bins are "
            "usually collected; collections are shifted by one day after public "
            "holidays. Optionally enter your municipality (as printed in the "
            "calendar) to also get its branch shredding (broyage de branches) date."
        ),
        "fr": (
            "Le calendrier du Pays de Craon indique uniquement si une semaine est "
            "une semaine Ordures Ménagères ou Emballages. Choisissez le jour où vos "
            "bacs sont habituellement collectés ; la collecte est décalée d'un jour "
            "après un jour férié. Indiquez éventuellement votre commune (comme "
            "imprimée dans le calendrier) pour obtenir aussi la date de broyage de "
            "branches."
        ),
    }

    REGIONS = (
        region(
            "Saint-Michel-de-la-Roë", commune="Saint-Michel-de-la-Roë", weekday="lundi"
        ),
    )

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _MEDIA_API_URL,
            params={
                "search": "calendrier-collecte",
                "per_page": 50,
                "_fields": "date,source_url",
            },
            raise_for_status=True,
            pick=_pdf_urls,
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url, timeout=60),
    )
    parse = parsers.EachResponse(ColourCellCalendarParser())
    preprocess = preprocessors.Compose(
        _collections, preprocessors.Deduplicate(), preprocessors.SortRows()
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
