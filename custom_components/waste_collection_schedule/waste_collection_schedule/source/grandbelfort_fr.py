"""Grand Belfort, France.

The agglomeration publishes one yearly PDF calendar per collection round on
https://www.grandbelfort.fr/prevention-et-valorisation-des-dechets/calendriers-de-collecte.html,
linked from the name of every commune it serves and, for the city of Belfort,
of every sector. Each calendar has twelve month grids whose collection days are
painted brown (household waste, bac brun) or yellow (packaging and paper, bac
jaune). The day numbers are drawn inside form objects, hence
``include_form_text``.
"""

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

_URL = "https://www.grandbelfort.fr"
_INDEX_URL = (
    f"{_URL}/prevention-et-valorisation-des-dechets/calendriers-de-collecte.html"
)

GENERAL = "Ordures ménagères"
PACKAGING = "Emballages et papiers"

_CELL = (12.0, 20.0)


def _name(link: Tag) -> str:
    """The commune, or 'Belfort - <sector>' for a sector of Belfort."""
    text = link.get_text(" ", strip=True)
    return f"Belfort - {text}" if "/Belfort/" in str(link.get("href")) else text


@final
class Source(BaseSource):
    TITLE = "Grand Belfort"
    DESCRIPTION = "Source for the Grand Belfort (Territoire de Belfort) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Cravanche": {"commune": "Cravanche"},
        "Évette-Salbert": {"commune": "Evette-Salbert"},
        "Belfort - La Pépinière": {"commune": "Belfort - La Pépinière"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your commune as listed on "
            "https://www.grandbelfort.fr/prevention-et-valorisation-des-dechets/calendriers-de-collecte.html, "
            "for example `Cravanche`. In Belfort use `Belfort - ` followed by "
            "your sector, for example `Belfort - La Pépinière`."
        ),
        "fr": (
            "Indiquez votre commune telle qu'elle figure sur "
            "https://www.grandbelfort.fr/prevention-et-valorisation-des-dechets/calendriers-de-collecte.html, "
            "par exemple `Cravanche`. À Belfort, indiquez `Belfort - ` suivi de "
            "votre secteur, par exemple `Belfort - La Pépinière`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "commune", href=r"/collectes20\d{2}[^/]*\.pdf$", label=_name
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(GENERAL, (0.1, 0.24, 0.3, 0.15), width=_CELL, height=_CELL),
            Marker(PACKAGING, (0.0, 0.2, 1.0, 0.0), width=_CELL, height=_CELL),
        ],
        placement="cell",
        year_pattern=r"collectes(20\d{2})",
        include_form_text=True,
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
