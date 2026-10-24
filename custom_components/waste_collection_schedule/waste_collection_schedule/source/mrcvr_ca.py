"""MRC de La Vallée-du-Richelieu, Québec, Canada.

The regional county municipality publishes one yearly PDF calendar per
municipality on
https://www.mrcvr.ca/services/matieres-residuelles/calendriers-des-collectes/.
Its twelve month grids (Monday to Friday) mark each collection with a symbol
behind the day number: a brown apple for food waste, a blue disc for
recycling, a black square for household waste, a green leaf for yard waste and
a red sofa for bulky items.
"""

from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.mrcvr.ca"
_INDEX_URL = f"{_URL}/services/matieres-residuelles/calendriers-des-collectes/"

FOOD = "Résidus alimentaires"
RECYCLING = "Récupération"
GENERAL = "Ordures"
GARDEN = "Résidus verts"
BULKY = "Encombrants"


@final
class Source(BaseSource):
    TITLE = "MRC de La Vallée-du-Richelieu"
    DESCRIPTION = (
        "Source for the MRC de La Vallée-du-Richelieu (Québec) collection calendars."
    )
    URL = _URL
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Otterburn Park": {"municipalite": "Otterburn Park"},
        "Saint-Basile-le-Grand": {"municipalite": "Saint-Basile-le-Grand"},
    }

    PARAMS = (config_params.municipality("municipalite"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your municipality as listed on "
            "https://www.mrcvr.ca/services/matieres-residuelles/calendriers-des-collectes/, "
            "for example `Otterburn Park`."
        ),
        "fr": (
            "Indiquez votre municipalité telle qu'elle figure sur "
            "https://www.mrcvr.ca/services/matieres-residuelles/calendriers-des-collectes/, "
            "par exemple `Otterburn Park`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "municipalite", href=r"Calendrier_collectes_\d{4}_.*\.pdf$"
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(FOOD, (0.56, 0.37, 0.26), width=(10, 16), height=(10, 16)),
            Marker(RECYCLING, (0.0, 0.31, 0.62), width=(11, 16), height=(11, 16)),
            # Partly hidden behind the recycling disc on a shared day.
            Marker(
                GENERAL,
                (0.0, 0.0, 0.01),
                tolerance=0.03,
                width=(7, 15),
                height=(5, 12),
            ),
            Marker(BULKY, (0.67, 0.09, 0.19), width=(9, 13), height=(6, 9)),
            Marker(GARDEN, (0.0, 0.42, 0.17), width=(7, 12), height=(7, 12)),
        ],
        placement="cell",
        year_pattern=r"collectes_(20\d{2})",
    )
    transform = ICSTransformer(
        type_value_map={
            FOOD: wt.FOOD_WASTE,
            RECYCLING: wt.RECYCLABLES,
            GENERAL: wt.GENERAL_WASTE,
            GARDEN: wt.GARDEN_WASTE,
            BULKY: wt.BULKY_WASTE,
        }
    )
