"""Ville de Chambly, Québec, Canada.

The city publishes one yearly PDF calendar per collection sector on
https://espacechambly.ca/info-collecte. Its twelve month grids mark each
collection with a symbol around the day number: a brown disc for organics, a
pink triangle for recyclables, a white bin for household waste (grey when bulky
items are collected with it), an orange square for dead leaves, a purple
hexagon for appliances and scrap metal (on request) and a red triangle for the
household hazardous waste drop-off.
"""

import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://espacechambly.ca"
_INDEX_URL = f"{_URL}/info-collecte"

ORGANICS = "Matières organiques"
RECYCLABLES = "Matières recyclables"
GENERAL = "Ordures"
BULKY = "Encombrants"
LEAVES = "Feuilles mortes et chaume"
APPLIANCES = "Électroménagers et métaux"
HAZARDOUS = "Résidus domestiques dangereux"

_SECTOR = re.compile(r"secteur\s*(\d)", re.IGNORECASE)


def _sector(link: Tag) -> str:
    """'Calendrier 2026 secteur 3' -> '3' (other links: '')."""
    match = _SECTOR.search(link.get_text(" ", strip=True))
    return match.group(1) if match else ""


@final
class Source(BaseSource):
    TITLE = "Ville de Chambly"
    DESCRIPTION = "Source for the Ville de Chambly (Québec) collection calendars."
    URL = _URL
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.ELECTRONICS,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Secteur 1": {"secteur": "1"},
        "Secteur 4": {"secteur": "4"},
    }

    PARAMS = (config_params.dropdown("secteur", ["1", "2", "3", "4"], label="Secteur"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Find your collection sector (1 to 4) on the sector map linked from "
            "https://espacechambly.ca/info-collecte and choose it."
        ),
        "fr": (
            "Trouvez votre secteur de collecte (1 à 4) sur la carte des secteurs "
            "accessible depuis https://espacechambly.ca/info-collecte et "
            "choisissez-le."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL, pick=lookups.link_pick("secteur", label=_sector)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(ORGANICS, (0.4, 0.65, 0.9, 0.35), width=(13, 18), height=(13, 18)),
            # The recyclables triangle has the sector's colour.
            *(
                Marker(RECYCLABLES, color, width=(7, 18), height=(13, 18))
                for color in (
                    (0.03, 0.73, 0.0, 0.0),
                    (0.99, 0.76, 0.04, 0.0),
                    (0.58, 0.0, 0.96, 0.0),
                    (0.52, 0.0, 0.0, 0.0),
                )
            ),
            Marker(
                GENERAL,
                (0.0, 0.0, 0.0, 0.0),
                tolerance=0.02,
                width=(11, 15),
                height=(10, 14),
            ),
            Marker(
                f"{GENERAL} + {BULKY}",
                (0.0, 0.0, 0.0, 0.6),
                width=(11, 15),
                height=(10, 14),
            ),
            Marker(LEAVES, (0.0, 0.52, 0.97, 0.0), width=(10, 14), height=(10, 14)),
            Marker(HAZARDOUS, (0.0, 1.0, 1.0, 0.0), width=(13, 17), height=(13, 17)),
            Marker(APPLIANCES, (0.5, 1.0, 0.0, 0.0), width=(8, 19), height=(13, 17)),
        ],
        placement="cell",
        year_pattern=r"calendriers-(20\d{2})",
    )
    preprocess = preprocessors.SplitLabels(r"\+")
    transform = ICSTransformer(
        type_value_map={
            ORGANICS: wt.ORGANIC,
            RECYCLABLES: wt.RECYCLABLES,
            GENERAL: wt.GENERAL_WASTE,
            BULKY: wt.BULKY_WASTE,
            LEAVES: wt.GARDEN_WASTE,
            APPLIANCES: wt.ELECTRONICS,
            HAZARDOUS: wt.HAZARDOUS,
        }
    )
