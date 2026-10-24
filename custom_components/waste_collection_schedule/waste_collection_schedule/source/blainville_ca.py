"""Ville de Blainville, Québec, Canada.

The city publishes one yearly PDF calendar for single-family homes and small
buildings (nine units or fewer), linked from
https://blainville.ca/services/environnement-et-voirie/collectes-et-matieres-residuelles.
Its twelve month grids mark each collection with a symbol around the day
number: a brown disc for organics, a black bin for household waste and a white
recycling disc for recyclables. Household waste and recyclables alternate on
Tuesdays in the south sector and on Wednesdays in the north sector; organics
are collected city-wide on Thursdays.
"""

import datetime
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://blainville.ca"
_INDEX_URL = (
    f"{_URL}/services/environnement-et-voirie/collectes-et-matieres-residuelles"
)

ORGANICS = "Matières organiques"
GENERAL = "Ordures ménagères"
RECYCLABLES = "Matières recyclables"

# The weekday of each sector's household waste and recyclables collection.
_SECTORS = {"Nord": 2, "Sud": 1}


def _sector_rows(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Keep the other sector's Tuesday or Wednesday collections out."""
    sector = _SECTORS[source.params["secteur"]] if source else None
    for day, label in rows:
        if (
            sector is not None
            and label != ORGANICS
            and day.weekday() in _SECTORS.values()
            and day.weekday() != sector
        ):
            continue
        yield day, label


@final
class Source(BaseSource):
    TITLE = "Ville de Blainville"
    DESCRIPTION = (
        "Source for the Ville de Blainville (Québec) residential collection calendar."
    )
    URL = _URL
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Secteur Nord": {"secteur": "Nord"},
        "Secteur Sud": {"secteur": "Sud"},
    }

    PARAMS = (config_params.dropdown("secteur", list(_SECTORS), label="Secteur"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Choose your sector (Nord or Sud) as shown on the map of the "
            "collection calendar on "
            "https://blainville.ca/services/environnement-et-voirie/collectes-et-matieres-residuelles: "
            "the north sector is collected on Wednesdays, the south sector on "
            "Tuesdays. The calendar covers homes and buildings of nine units or "
            "fewer."
        ),
        "fr": (
            "Choisissez votre secteur (Nord ou Sud) selon la carte du calendrier "
            "des collectes sur "
            "https://blainville.ca/services/environnement-et-voirie/collectes-et-matieres-residuelles : "
            "le secteur nord est collecté le mercredi, le secteur sud le mardi. "
            "Le calendrier concerne les résidences de neuf logements et moins."
        ),
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_INDEX_URL,
        pattern=r"calendrier_collectes_(\d{4})\.pdf",
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(ORGANICS, (0.54, 0.34, 0.2), width=(12, 17), height=(12, 17)),
            Marker(GENERAL, (0.14, 0.12, 0.13), width=(12, 17), height=(12, 17)),
            Marker(
                RECYCLABLES,
                (1.0, 1.0, 1.0),
                tolerance=0.02,
                width=(15, 17),
                height=(13, 15),
            ),
        ],
        placement="cell",
        year_pattern=r"collectes_(20\d{2})",
    )
    preprocess = staticmethod(_sector_rows)
    transform = ICSTransformer(
        type_value_map={
            ORGANICS: wt.ORGANIC,
            GENERAL: wt.GENERAL_WASTE,
            RECYCLABLES: wt.RECYCLABLES,
        }
    )
