"""Communauté de Communes du Pays de Mormal, France.

The intercommunality publishes one yearly PDF calendar per collection round on
https://www.cc-paysdemormal.fr/calendriers-de-collecte/, linked from a card per
commune. Each calendar has a column per month and a row per day; a grey square
marks the household-waste collection and a yellow dot the packaging (bac de tri)
collection. In the towns where the packaging week depends on the street (Bavay,
Landrecies, Le Quesnoy, ...) the calendar marks every week and prints the even
and odd weeks as coloured bars, so the resident picks their week.
"""

import datetime
from collections.abc import Iterable
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.cc-paysdemormal.fr"
_INDEX_URL = f"{_URL}/calendriers-de-collecte/"

GENERAL = "Ordures ménagères"
PACKAGING = "Bac de tri"

_WEEKS = {"paire": 0, "impaire": 1}

_COMMUNES = (
    "Audignies",
    "Bavay",
    "Beaudignies",
    "Bellignies",
    "Bettrechies",
    "Bousies",
    "Bry",
    "Croix-Caluyau",
    "Englefontaine",
    "Eth",
    "Fontaine-au-Bois",
    "Forest-en-Cambrésis",
    "Frasnoy",
    "Ghissignies",
    "Gommegnies",
    "Gussignies",
    "Hargnies",
    "Hecq",
    "Hon-Hergies",
    "Houdain-lez-Bavay",
    "Jenlain",
    "Jolimetz",
    "La Flamengrie",
    "La Longueville",
    "Landrecies",
    "Le Favril",
    "Le Quesnoy",
    "Locquignol",
    "L'Orée de Mormal (ex Amfroipret)",
    "L'Orée de Mormal (ex Bermeries)",
    "Louvignies-Quesnoy",
    "Maresches",
    "Maroilles",
    "Mecquignies",
    "Neuville-en-Avesnois",
    "Obies",
    "Orsinval",
    "Poix-du-Nord",
    "Potelle",
    "Preux-au-Bois",
    "Preux-au-Sart",
    "Raucourt-au-Bois",
    "Robersart",
    "Ruesnes",
    "Saint-Waast-la-Vallée",
    "Salesches",
    "Sepmeries",
    "Taisnières-sur-Hon",
    "Vendegies-au-Bois",
    "Villereau",
    "Villers-Pol",
    "Wargnies-le-Grand",
    "Wargnies-le-Petit",
)


def _card_title(link: Tag) -> str:
    heading = link.find("h4")
    return heading.get_text(" ", strip=True) if heading else ""


def _rows(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Keep the resident's packaging week where the calendar marks every week."""
    packaging = [day for day, label in rows if label == PACKAGING]
    weekly = len({day.isocalendar()[1] for day in packaging}) > 40
    week = (source.params.get("semaine") if source else None) or None
    if weekly and week is None:
        raise SourceArgumentRequired(
            "semaine",
            "the packaging collection of this commune depends on the street: "
            "choose 'paire' or 'impaire' as shown on the map of the calendar",
        )
    for day, label in rows:
        if (
            label == PACKAGING
            and weekly
            and week is not None
            and day.isocalendar()[1] % 2 != _WEEKS[week]
        ):
            continue
        yield day, label


@final
class Source(BaseSource):
    TITLE = "Communauté de Communes du Pays de Mormal"
    DESCRIPTION = "Source for the Pays de Mormal (Nord) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Frasnoy": {"commune": "Frasnoy"},
        "Audignies": {"commune": "Audignies"},
        "Bavay, semaine impaire": {"commune": "Bavay", "semaine": "impaire"},
    }

    PARAMS = (
        config_params.municipality("commune"),
        config_params.dropdown("semaine", list(_WEEKS), label="Semaine", optional=True),
    )

    REGIONS = tuple(region(commune, commune=commune) for commune in _COMMUNES)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune as listed on "
            "https://www.cc-paysdemormal.fr/calendriers-de-collecte/. In Bavay, "
            "La Longueville, Landrecies, Le Quesnoy and Poix-du-Nord the packaging "
            "(bac de tri) week depends on your street: look it up on the map of "
            "the calendar and set `semaine` to `paire` (even weeks) or `impaire` "
            "(odd weeks). Leave it empty elsewhere."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure sur "
            "https://www.cc-paysdemormal.fr/calendriers-de-collecte/. À Bavay, "
            "La Longueville, Landrecies, Le Quesnoy et Poix-du-Nord, la semaine "
            "du bac de tri dépend de votre rue : consultez le plan au verso du "
            "calendrier et choisissez `semaine` `paire` ou `impaire`. Laissez le "
            "champ vide ailleurs."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "commune", selector="div.c-card a[href]", label=_card_title
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(GENERAL, (0.52, 0.51, 0.51), width=(4, 9), height=(4, 9)),
            Marker(PACKAGING, (1.0, 0.84, 0.07), width=(4, 9), height=(4, 9)),
        ],
        year_pattern=r"COLLECTE_(20\d{2})",
        weekdays="LMMJVSD",
        pages=(0,),
    )
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
