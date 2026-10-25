"""Douaisis Agglo, France.

The agglomeration publishes one yearly PDF calendar per commune (Douai per
sector) on
https://www.douaisis-agglo.com/services/dechets/calendriers-de-collecte-de-votre-commune.
Each calendar has a column per month and a row per day (``1 J``); small coloured
squares beside the day mark the collections: yellow recyclables, grey household
waste, blue glass, brown garden waste and orange bulky waste.
"""

import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.douaisis-agglo.com"
_INDEX_URL = f"{_URL}/services/dechets/calendriers-de-collecte-de-votre-commune"

RECYCLABLES = "Recyclables"
GENERAL = "Ordures ménagères"
GLASS = "Verre"
GARDEN = "Déchets végétaux"
BULKY = "Encombrants"

_SQUARE = (3.0, 8.0)
_TITLE_SUFFIX = re.compile(r"\s+calendrier\s.*$", re.IGNORECASE)


def _commune(link: Tag) -> str:
    """'Auby calendrier des déchets 2026' -> 'Auby'."""
    return _TITLE_SUFFIX.sub("", link.get_text(" ", strip=True))


@final
class Source(BaseSource):
    TITLE = "Douaisis Agglo"
    DESCRIPTION = "Source for the Douaisis Agglo (Nord) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Flines-lez-Râches": {"commune": "Flines-lez-Râches"},
        "Goeulzin": {"commune": "Goeulzin"},
        "Douai - Hyper-centre": {"commune": "Douai - Hyper-centre"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune as listed on "
            "https://www.douaisis-agglo.com/services/dechets/calendriers-de-collecte-de-votre-commune, "
            "for example `Flines-lez-Râches`. In Douai use the sector, for "
            "example `Douai - Dorignies`."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure sur "
            "https://www.douaisis-agglo.com/services/dechets/calendriers-de-collecte-de-votre-commune, "
            "par exemple `Flines-lez-Râches`. À Douai, indiquez le secteur, par "
            "exemple `Douai - Dorignies`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL, pick=lookups.link_pick("commune", label=_commune)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(RECYCLABLES, (1.0, 0.88, 0.0), width=_SQUARE, height=_SQUARE),
            Marker(GENERAL, (0.66, 0.65, 0.65), width=_SQUARE, height=_SQUARE),
            Marker(GLASS, (0.0, 0.48, 0.77), width=_SQUARE, height=_SQUARE),
            Marker(GARDEN, (0.49, 0.27, 0.03), width=_SQUARE, height=_SQUARE),
            Marker(BULKY, (0.94, 0.49, 0.1), width=_SQUARE, height=_SQUARE),
        ],
        year_pattern=r"/(20\d{2})/",
        weekdays="LMMJVSD",
    )
    transform = ICSTransformer(
        type_value_map={
            RECYCLABLES: wt.RECYCLABLES,
            GENERAL: wt.GENERAL_WASTE,
            GLASS: wt.GLASS,
            GARDEN: wt.GARDEN_WASTE,
            BULKY: wt.BULKY_WASTE,
        }
    )
