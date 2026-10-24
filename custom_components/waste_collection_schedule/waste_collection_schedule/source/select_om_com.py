"""Select'om (SMICTOM de la région de Molsheim), France.

Select'om publishes one PDF calendar per commune on
https://www.select-om.com/le-selectom-vous/calendrier-des-collectes/. Its twelve
month grids paint the collection days grey (household waste) or yellow
(packaging, paper and cardboard); a weekday collected several weeks in a row is
painted as one bar down its column. The weekday heading of each column also
settles the year of a calendar that names another one in its text.
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

_URL = "https://www.select-om.com"
_INDEX_URL = f"{_URL}/le-selectom-vous/calendrier-des-collectes/"

GENERAL = "Ordures ménagères"
PACKAGING = "Collecte sélective"


@final
class Source(BaseSource):
    TITLE = "Select'om"
    DESCRIPTION = "Source for the Select'om (Bas-Rhin) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Molsheim": {"commune": "Molsheim"},
        "Bischoffsheim": {"commune": "Bischoffsheim"},
        "Schirmeck": {"commune": "Schirmeck"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune as listed on "
            "https://www.select-om.com/le-selectom-vous/calendrier-des-collectes/, "
            "for example `Molsheim`."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure sur "
            "https://www.select-om.com/le-selectom-vous/calendrier-des-collectes/, "
            "par exemple `Molsheim`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick("commune", href=r"/uploads/.*\.pdf$"),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    # The calendars come from two designs, and the one marking a change of
    # rhythm paints the months after it in paler tints.
    parse = MarkerCalendarParser(
        [
            *(
                Marker(label, color, tolerance=0.04, width=(15, 20), height=(8, 60))
                for label, color in (
                    (GENERAL, (0.2, 0.13, 0.2, 0.0)),
                    (GENERAL, (0.12, 0.08, 0.12, 0.0)),
                    (GENERAL, (0.83, 0.84, 0.81)),
                    (PACKAGING, (0.0, 0.2, 1.0, 0.0)),
                    (PACKAGING, (0.0, 0.12, 0.6, 0.0)),
                    (PACKAGING, (1.0, 0.8, 0.0)),
                )
            ),
        ],
        placement="cell",
        weekdays=("LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"),
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
