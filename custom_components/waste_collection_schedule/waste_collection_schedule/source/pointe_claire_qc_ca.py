"""Pointe-Claire's official dated ICS calendars, selected by collection sector.

Use the shared ICS engine and transformer, with the provider UID taking
precedence over accent-insensitive title keywords. Unknown titles survive
unchanged; leaf and Christmas tree pickups retain the garden-waste category.
"""

import re
import unicodedata
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import ICSTransformer

_SECTOR_URL_MAP: dict[str, str] = {
    "A": "https://espace.pointe-claire.ca/avis/collectes/v2/calendrier.ics?collects=2",  # codespell:ignore espace
    "B": "https://espace.pointe-claire.ca/avis/collectes/v2/calendrier.ics?collects=3",  # codespell:ignore espace
}


def _sector_url(sector: str, **_) -> str:
    key = str(sector).upper().strip()
    url = _SECTOR_URL_MAP.get(key)
    if url is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "sector", sector, list(_SECTOR_URL_MAP.keys())
        )
    return url


_UID_LABELS = {
    "dechets": "Déchets domestiques",
    "compost": "Matières organiques",
    "recyclage": "Recyclage",
    "encombrants": "Encombrants",
    "verts": "Feuilles",
    "noel": "Arbre de Noël",
}
_UID_CODE_RE = re.compile(r"-([a-z_]+)@", re.IGNORECASE)
_TITLE_KEYWORDS = (
    (("noel", "sapin"), "Arbre de Noël"),
    (("feuille", "vert"), "Feuilles"),
    (("organique", "compost", "alimentaire"), "Matières organiques"),
    (("recycl",), "Recyclage"),
    (("encombr",), "Encombrants"),
    (("dechet", "ordure"), "Déchets domestiques"),
)


def _collection_label(value: str) -> str:
    """Clean the UID/newline/SUMMARY pair rendered by the shared ICS parser."""
    uid, separator, title = value.partition("\n")
    if not separator:
        title, uid = uid, ""
    title = title.strip()
    match = _UID_CODE_RE.search(uid)
    if match and match.group(1).lower() in _UID_LABELS:
        return _UID_LABELS[match.group(1).lower()]

    normalized = (
        unicodedata.normalize("NFKD", title)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    for keywords, label in _TITLE_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return label
    return title


@final
class Source(BaseSource):
    TITLE = "Pointe-Claire (QC)"
    DESCRIPTION = "Source for Pointe-Claire, Québec waste collection schedules."
    URL = "https://www.pointe-claire.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Sector A": {"sector": "A"},
        "Sector B": {"sector": "B"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Find your collection sector (A or B) with the City's address search:"
            " https://www.pointe-claire.ca/en/community-life/citizen-services/"
            "search-by-address. Leaf and Christmas tree collections use the"
            " garden-waste category. Mattress and ecocentre days are not included"
            " in the city feed."
        ),
        "fr": (
            "Trouvez votre secteur de collecte (A ou B) avec l'outil de recherche"
            " par adresse de la Ville de Pointe-Claire :"
            " https://www.pointe-claire.ca/vie-communautaire/services-aux-citoyens/"
            "recherche-par-adresse"
        ),
    }

    PARAMS = (dropdown("sector", ["A", "B"], label="Sector"),)

    retrieve = Request(url=_sector_url)
    # UID cannot contain a literal newline; SUMMARY may, and is kept after it.
    parse = parsers.IcsParser(
        min_events=1,
        title_template="{{date.uid or ''}}\n{{date.summary or ''}}",
    )
    # Remove the UID carrier before the transformer retains the provider label.
    preprocess = preprocessors.RowRelabel(rename=_collection_label)
    transform = ICSTransformer(
        type_value_map={
            "Matières organiques": wt.ORGANIC,
            "Recyclage": wt.RECYCLABLES,
            "Déchets domestiques": wt.GENERAL_WASTE,
            "Encombrants": wt.BULKY_WASTE,
            "Arbre de Noël": wt.GARDEN_WASTE,
            "Collecte de feuilles": wt.GARDEN_WASTE,
            "Feuilles": wt.GARDEN_WASTE,
            "": None,
        },
    )
