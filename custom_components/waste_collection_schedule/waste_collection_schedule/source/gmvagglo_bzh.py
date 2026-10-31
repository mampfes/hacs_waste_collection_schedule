"""Golfe du Morbihan - Vannes agglomération, France.

The agglomeration links one yearly PDF calendar per commune (or sector) from
https://www.golfedumorbihan-vannesagglomeration.bzh/mon-quotidien/dechets/collecte/.
Its twelve month grids mark each collection with a disc behind the day number:
green for household waste (bac vert) and yellow for packaging and paper (bac
jaune). The day numbers and headings are drawn inside form objects, hence
``include_form_text``.
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

_URL = "https://www.golfedumorbihan-vannesagglomeration.bzh"
_INDEX_URL = f"{_URL}/mon-quotidien/dechets/collecte/"

GENERAL = "Ordures ménagères"
PACKAGING = "Emballages et papiers"

_DISC = (10.0, 18.0)


@final
class Source(BaseSource):
    TITLE = "Golfe du Morbihan - Vannes agglomération"
    DESCRIPTION = "Source for the Golfe du Morbihan - Vannes agglomération collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Ploeren": {"commune": "Ploeren"},
        "Vannes secteur 3": {"commune": "Vannes secteur 3"},
        "Séné secteur 1": {"commune": "Séné secteur 1"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune (or sector) as listed under 'Calendriers de "
            "collecte' on "
            "https://www.golfedumorbihan-vannesagglomeration.bzh/mon-quotidien/dechets/collecte/, "
            "for example `Ploeren` or `Vannes secteur 3`."
        ),
        "fr": (
            "Indiquez votre commune (ou secteur) telle qu'elle figure sous "
            "« Calendriers de collecte » sur "
            "https://www.golfedumorbihan-vannesagglomeration.bzh/mon-quotidien/dechets/collecte/, "
            "par exemple `Ploeren` ou `Vannes secteur 3`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick("commune", href=r"/calendrier-collecte"),
            ),
        ),
        # The commune's page redirects to its current calendar PDF.
        url=lambda calendar_url, **_: calendar_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(GENERAL, (0.0, 0.56, 0.42), width=_DISC, height=_DISC),
            Marker(PACKAGING, (1.0, 0.86, 0.0), width=_DISC, height=_DISC),
        ],
        placement="cell",
        year_pattern=r"COLLECTE\s*(20\d{2})",
        include_form_text=True,
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
