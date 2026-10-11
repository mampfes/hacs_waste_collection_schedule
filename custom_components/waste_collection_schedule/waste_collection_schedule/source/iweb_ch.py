"""Swiss municipalities on the i-web CMS, read from their ``/abfalldaten`` page.

Many Swiss municipalities run their website on the i-web CMS, whose
``/abfalldaten`` page carries the dated collections as JSON in a
``data-entities`` attribute (see :mod:`..service.IWeb`). The page and its
payload are the same on every i-web site, so instead of one near-identical
module per municipality this source takes the municipality's website as its
argument, and the municipalities known to work are listed as regions in
``doc/regions/iweb_ch.yaml``. Adding a municipality is a line in that file.

Only the dated table is read. Collections that i-web lists as "regular"
(weekly rounds described in prose on a detail page) are not projected here;
municipalities whose regular pages follow the "wöchentlich am <Tag>" wording
are served by dedicated modules on ``IWebRegular`` (seuzach_ch).

Labels differ per municipality and often carry a qualifier ("Papiersammlung
(Pfadfinder)", "Kehrichtabfuhr Zone II (Bremgarten)"). They are mapped by
their leading keyword, and the provider's own label is kept on the collection
so rounds of one type (two paper drives, two refuse zones) stay apart.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.IWeb import (
    AbfalldatenRows,
    abfalldaten_parser,
)
from waste_collection_schedule.transformers import ICSTransformer

# Leading keyword of an i-web label -> the key it is mapped under. Checked in
# order, case-insensitively, against the start of the label.
_KEYWORDS: tuple[tuple[str, str], ...] = (
    (r"(haus)?kehricht", "Kehricht"),
    (r"(alt)?papier|karton", "Papier"),
    (r"grün(abfuhr|gut)|garten", "Grüngut"),
    (r"häcksel", "Häckseldienst"),
    (r"sonderabf", "Sonderabfall"),
    (r"(alt)?metall|alteisen", "Altmetall"),
)
_KEYWORD_RE = [(re.compile(pattern, re.IGNORECASE), key) for pattern, key in _KEYWORDS]


def _keyword(label: str) -> str:
    text = label.strip()
    for pattern, key in _KEYWORD_RE:
        if pattern.match(text):
            return key
    return text


def _website(value: object) -> str:
    """Normalise the website argument to ``https://host`` without a path."""
    text = str(value).strip().rstrip("/")
    text = re.sub(r"/abfalldaten$", "", text, flags=re.IGNORECASE)
    if not re.match(r"https?://", text, re.IGNORECASE):
        text = f"https://{text}"
    return text


@final
class Source(BaseSource):
    TITLE = "i-web (Swiss municipalities)"
    DESCRIPTION = (
        "Source for Swiss municipalities whose website runs on the i-web CMS "
        "and lists collection dates on its /abfalldaten page."
    )
    URL = "https://www.i-web.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Uetikon am See": {"website": "https://www.uetikonamsee.ch"},
        "Flums": {"website": "www.flums.ch"},
        "Bremgarten AG": {"website": "https://www.bremgarten.ch/abfalldaten"},
    }

    PARAMS = (text_field("website", "Website", coerce=_website),)

    REGIONS = regions.from_yaml("iweb_ch", website="website")

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality's website, e.g. https://www.flums.ch. It "
            "works if https://<website>/abfalldaten shows a table of collection "
            "dates."
        ),
        "de": (
            "Geben Sie die Website Ihrer Gemeinde ein, z. B. https://www.flums.ch. "
            "Das funktioniert, wenn https://<website>/abfalldaten eine Tabelle "
            "mit Abfuhrdaten zeigt."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        wt.METAL,
    ]

    retrieve = HttpGetRetriever(url=lambda website, **_: f"{website}/abfalldaten")
    parse = abfalldaten_parser()
    # A collection over several days (a paper drive over a weekend) is one
    # collection per day.
    preprocess = AbfalldatenRows(expand_ranges=True)
    transform = ICSTransformer(
        clean=_keyword,
        carry_raw_label=True,
        type_value_map={
            "Kehricht": wt.GENERAL_WASTE,
            "Papier": wt.PAPER,
            "Grüngut": wt.GARDEN_WASTE,
            "Häckseldienst": wt.GARDEN_WASTE,
            "Sonderabfall": wt.HAZARDOUS,
            "Altmetall": wt.METAL,
        },
    )
