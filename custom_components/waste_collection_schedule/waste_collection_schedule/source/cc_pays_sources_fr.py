"""Communauté de Communes du Pays des Sources, France.

The intercommunality publishes one yearly PDF calendar per collection zone on
https://www.cc-pays-sources.fr/environnement/gestion-des-dechets/votre-calendrier-de-tri/,
whose drop-down links every commune to its zone's calendar. Each calendar has a
column per month and a row per day (``JEU 1``); a grey "O.M." badge marks the
household waste collection and a yellow "J" badge the packaging (bac jaune)
collection. January to June are on the first page, July to December on the
second; the text is drawn inside form objects, hence ``include_form_text``.
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

_URL = "https://www.cc-pays-sources.fr"
_INDEX_URL = f"{_URL}/environnement/gestion-des-dechets/votre-calendrier-de-tri/"

GENERAL = "Ordures ménagères"
PACKAGING = "Bac jaune"


@final
class Source(BaseSource):
    TITLE = "Communauté de Communes du Pays des Sources"
    DESCRIPTION = "Source for the Pays des Sources (Oise) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Ressons-sur-Matz": {"commune": "Ressons-sur-Matz"},
        "Lassigny": {"commune": "Lassigny"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune as listed in the drop-down on "
            "https://www.cc-pays-sources.fr/environnement/gestion-des-dechets/votre-calendrier-de-tri/, "
            "for example `Ressons-sur-Matz`."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure dans la liste sur "
            "https://www.cc-pays-sources.fr/environnement/gestion-des-dechets/votre-calendrier-de-tri/, "
            "par exemple `Ressons-sur-Matz`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "commune", selector="select option[value]", attribute="value"
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(GENERAL, (0.41, 0.41, 0.41), width=(18, 28), height=(8, 14)),
            Marker(PACKAGING, (0.97, 0.69, 0.16), width=(9, 13), height=(9, 13)),
        ],
        year_pattern=r"calendrier(20\d{2})",
        weekdays=("LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"),
        row_reach=90,
        include_form_text=True,
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
