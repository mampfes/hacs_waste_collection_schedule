"""Communauté de communes Val ès Dunes, France.

The intercommunality publishes one yearly PDF calendar per commune on
https://www.valesdunes.fr/calendriers-de-collecte/. Each calendar has a column
per month and a row per day; a dark grey dot beside the day marks the household
waste (bac gris) collection and a yellow dot the packaging (bac jaune)
collection. The day numbers are drawn inside form objects, hence
``include_form_text``.
"""

from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.valesdunes.fr"
_INDEX_URL = f"{_URL}/calendriers-de-collecte/"

GENERAL = "Ordures ménagères"
PACKAGING = "Emballages et papiers"

_COMMUNES = (
    "Argences",
    "Banneville-la-Campagne",
    "Bellengreville",
    "Cagny",
    "Canteloup",
    "Cesny-aux-Vignes",
    "Cléville",
    "Condé-sur-Ifs",
    "Emiéville",
    "Frénouville",
    "Janville",
    "Moult-Chicheboville",
    "Ouézy",
    "Saint-Ouen-du-Mesnil-Oger",
    "Saint-Pair",
    "Saint-Pierre-du-Jonquet",
    "Saint-Sylvain",
    "Valambray",
    "Vimont",
)


@final
class Source(BaseSource):
    TITLE = "Val ès Dunes"
    DESCRIPTION = "Source for the Val ès Dunes (Calvados) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Bellengreville": {"commune": "Bellengreville"},
        "Saint-Pierre-du-Jonquet": {"commune": "Saint-Pierre-du-Jonquet"},
    }

    PARAMS = (config_params.municipality("commune"),)

    REGIONS = tuple(region(commune, commune=commune) for commune in _COMMUNES)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune as listed on "
            "https://www.valesdunes.fr/calendriers-de-collecte/, for example "
            "`Bellengreville`."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure sur "
            "https://www.valesdunes.fr/calendriers-de-collecte/, par exemple "
            "`Bellengreville`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_INDEX_URL, pick=lookups.link_pick("commune")),),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(GENERAL, (0.34, 0.34, 0.34), width=(5, 10), height=(5, 10)),
            Marker(PACKAGING, (1.0, 0.77, 0.0), width=(5, 10), height=(5, 10)),
        ],
        weekdays="LMMJVSD",
        include_form_text=True,
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
