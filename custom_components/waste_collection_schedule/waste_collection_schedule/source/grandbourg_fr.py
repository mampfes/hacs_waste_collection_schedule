"""Grand Bourg Agglomération, France.

The agglomeration publishes one yearly PDF calendar per commune (or commune
sector) on https://www.grandbourg.fr/26-collecte-des-ordures-menageres.htm:
twelve month grids whose collection days are painted grey (household waste) or
yellow (recyclables). Bourg-en-Bresse, Péronnas, Saint-Denis-lès-Bourg and
Viriat only publish a street map, not a calendar.
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

_URL = "https://www.grandbourg.fr"
_INDEX_URL = f"{_URL}/26-collecte-des-ordures-menageres.htm"

GENERAL = "Ordures ménagères"
RECYCLABLES = "Déchets recyclables"

_CELL_WIDTH = (18.0, 28.0)
_CELL_HEIGHT = (10.0, 18.0)


@final
class Source(BaseSource):
    TITLE = "Grand Bourg Agglomération"
    DESCRIPTION = (
        "Source for the Grand Bourg Agglomération (Ain) collection calendars, France."
    )
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Courtes": {"commune": "Courtes"},
        "Attignat Est Crangeat": {"commune": "Attignat Est Crangeat"},
        "Saint-Martin-du-Mont": {"commune": "Saint-Martin-du-Mont"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune (or commune sector) as listed under the "
            "collection calendars on "
            "https://www.grandbourg.fr/26-collecte-des-ordures-menageres.htm, "
            "for example `Courtes` or `Attignat Est Crangeat`."
        ),
        "fr": (
            "Indiquez votre commune (ou secteur) telle qu'elle figure dans la "
            "liste des calendriers de collecte sur "
            "https://www.grandbourg.fr/26-collecte-des-ordures-menageres.htm, "
            "par exemple `Courtes` ou `Attignat Est Crangeat`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL, pick=lookups.link_pick("commune", href=r"\.pdf$")
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(
                GENERAL, (0.0, 0.0, 0.0, 0.5), width=_CELL_WIDTH, height=_CELL_HEIGHT
            ),
            Marker(
                RECYCLABLES,
                (0.02, 0.22, 0.93, 0.0),
                width=_CELL_WIDTH,
                height=_CELL_HEIGHT,
            ),
        ],
        placement="cell",
        year_pattern=r"D[ÉE]CHETS\s+(20\d{2})",
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, RECYCLABLES: wt.RECYCLABLES}
    )
