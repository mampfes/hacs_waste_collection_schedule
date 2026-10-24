"""SIVOM du Louhannais, France.

The SIVOM publishes one yearly PDF calendar per collection weekday on
https://sivom-louhannais.fr/collecte-des-omr/les-calendriers-de-collecte.html,
each listing the communes collected that day: twelve month grids whose
collection days are painted grey (household waste, bac gris) or yellow
(packaging and paper, bac jaune). A crossed-out holiday moves the collection to
the Saturday, which the calendar paints instead.

Louhans-Châteaurenaud has a calendar of its own, by street zone, which this
source does not read.
"""

import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://sivom-louhannais.fr"
_INDEX_URL = f"{_URL}/collecte-des-omr/les-calendriers-de-collecte.html"

GENERAL = "Ordures ménagères"
PACKAGING = "Emballages et papiers"

_DAY = re.compile(r"COLLECTE\s+DU\s+(\w+)\s+20\d{2}", re.IGNORECASE)

_COMMUNES = {
    "Lundi": (
        "Branges",
        "Cuisery",
        "Huilly-sur-Seille",
        "La Frette",
        "L'Abergement-de-Cuisery",
        "Loisy",
        "Ormes",
        "Saint-André",
        "Savigny-sur-Seille",
        "Simandre",
    ),
    "Mardi": (
        "Bantanges",
        "La Chapelle-Naude",
        "Ménetreuil",
        "Montcony",
        "Rancy",
        "Savigny-en-Revermont",
        "Saint-Usuge",
        "Sornay",
    ),
    "Mercredi": (
        "Bruailles",
        "Frontenaud",
        "Le Miroir",
        "Saint-Martin-du-Mont",
        "Sagy",
        "Vincelles",
    ),
    "Jeudi": (
        "Brienne",
        "Jouvençon",
        "La Chapelle-Thècle",
        "La Genête",
        "Le Fay",
        "Montagny-près-Louhans",
        "Montpont-en-Bresse",
        "Montret",
        "Ratenelle",
        "Ratte",
        "Romenay",
        "Saint-Vincent-en-Bresse",
    ),
    "Vendredi": (
        "Beaurepaire-en-Bresse",
        "Champagnat",
        "Condal",
        "Cuiseaux",
        "Dommartin-lès-Cuiseaux",
        "Flacey-en-Bresse",
        "Joudes",
        "Saillenard",
        "Sainte-Croix",
        "Varennes-Saint-Sauveur",
    ),
}


def _weekday(link: Tag) -> str:
    """'CALENDRIER DE COLLECTE DU MARDI 2026' -> 'MARDI' (other links: '')."""
    match = _DAY.search(link.get_text(" ", strip=True))
    return match.group(1) if match else ""


@final
class Source(BaseSource):
    TITLE = "SIVOM du Louhannais"
    DESCRIPTION = "Source for the SIVOM du Louhannais (Saône-et-Loire) collection calendars, France."
    URL = _URL
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Vendredi (Beaurepaire-en-Bresse)": {"jour": "Vendredi"},
        "Lundi (Cuisery)": {"jour": "Lundi"},
    }

    PARAMS = (
        config_params.dropdown("jour", list(_COMMUNES), label="Jour de collecte"),
    )

    REGIONS = tuple(
        region(commune, jour=day)
        for day, communes in _COMMUNES.items()
        for commune in communes
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Choose your commune's collection weekday as listed on "
            "https://sivom-louhannais.fr/collecte-des-omr/les-calendriers-de-collecte.html "
            "(for example Beaurepaire-en-Bresse: `Vendredi`)."
        ),
        "fr": (
            "Choisissez le jour de collecte de votre commune tel qu'indiqué sur "
            "https://sivom-louhannais.fr/collecte-des-omr/les-calendriers-de-collecte.html "
            "(par exemple Beaurepaire-en-Bresse : `Vendredi`)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL, pick=lookups.link_pick("jour", label=_weekday)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(GENERAL, (0.51, 0.39, 0.39, 0.21), width=(14, 22), height=(9, 15)),
            Marker(PACKAGING, (0.06, 0.16, 0.91, 0.0), width=(14, 22), height=(9, 15)),
        ],
        placement="cell",
        year_pattern=r"-(20\d{2})-",
    )
    transform = ICSTransformer(
        type_value_map={GENERAL: wt.GENERAL_WASTE, PACKAGING: wt.RECYCLABLES}
    )
