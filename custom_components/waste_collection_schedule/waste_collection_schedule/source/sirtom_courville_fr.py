"""SIRTOM de la région de Courville-sur-Eure, France.

The SIRTOM publishes one yearly PDF calendar per commune, and separate ones for
hamlets collected on other days ("exceptions"), on
https://www.sirtom-courville.fr/mes-dechets/jours-de-collecte/. Each calendar
has a column per month and a row per day (``JE 1``); a black pill marks the
household waste (bac noir) collection and a yellow triangle the packaging (bac
jaune) collection. January to June are on the first page, July to December on
the second.
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

_URL = "https://www.sirtom-courville.fr"
_INDEX_URL = f"{_URL}/mes-dechets/jours-de-collecte/"

GENERAL = "Ordures ménagères"
PACKAGING = "Tri sélectif"

_TRAILING_YEAR = re.compile(r"\s*[–-]?\s*(?:20\d{2})?\s*$")


def _calendar_name(link: Tag) -> str:
    """'Téléchargez le calendrier des collectes : Digny – 2026' -> 'Digny'."""
    heading = link.select_one(".elementor-heading-title")
    text = heading.get_text(" ", strip=True) if heading else ""
    return _TRAILING_YEAR.sub("", text.split(":", 1)[-1]).strip()


@final
class Source(BaseSource):
    TITLE = "SIRTOM de Courville-sur-Eure"
    DESCRIPTION = "Source for the SIRTOM de Courville-sur-Eure (Eure-et-Loir), France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Fontaine-la-Guyon": {"commune": "Fontaine-la-Guyon"},
        "Digny, Les Hauts Cornets": {"commune": "Digny – Les Hauts Cornets, La Gatine"},
        "Senonches": {"commune": "Senonches"},
    }

    PARAMS = (config_params.municipality("commune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open https://www.sirtom-courville.fr/mes-dechets/jours-de-collecte/ "
            "and enter the name of your calendar as printed after 'Téléchargez le "
            "calendrier des collectes :', without the year, for example "
            "`Fontaine-la-Guyon`. Hamlets with their own calendar include it, for "
            "example `Digny – Les Hauts Cornets, La Gatine`."
        ),
        "fr": (
            "Ouvrez https://www.sirtom-courville.fr/mes-dechets/jours-de-collecte/ "
            "et indiquez le nom de votre calendrier tel qu'il figure après "
            "« Téléchargez le calendrier des collectes : », sans l'année, par "
            "exemple `Fontaine-la-Guyon`. Les hameaux ayant leur propre calendrier "
            "l'ajoutent, par exemple `Digny – Les Hauts Cornets, La Gatine`."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick("commune", label=_calendar_name),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(
                GENERAL, (0.0, 0.0, 0.0), tolerance=0.05, width=(10, 18), height=(5, 9)
            ),
            Marker(PACKAGING, (1.0, 0.75, 0.0), width=(5, 12), height=(5, 12)),
        ],
        year_pattern=r"_(20\d{2})\.pdf",
        weekdays=("LU", "MA", "ME", "JE", "VE", "SA", "DI"),
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
