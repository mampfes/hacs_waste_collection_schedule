"""Ekoland Polska (Kraśnik), Poland.

Ekoland publishes one yearly schedule PDF per municipality on
https://www.ekolandpolska.com.pl/dla-mieszkancow/odbior-odpadow-gminy
("harmonogram-miasto-krasnik-2026.pdf"). The source reads the index page and
fetches the configured municipality's detached-house (zabudowa jednorodzinna)
PDFs from this year on (``retrievers.yearly_links``), so once next year's PDF
is linked the rest of this year is still read; the street's rows are merged
across them.

Each PDF is one Excel-exported table: a header row of month names, then one
block per area (numbered "lp."), whose left cell lists the area's streets and
whose rows name a waste type followed by that month's days ("5, 19"). The
shared ``preprocessors.PdfRoundMonthGrid`` reads it into blocks (page by page,
as long lists continue on a second page); the source only picks the block
listing the configured street.
"""

import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://www.ekolandpolska.com.pl/dla-mieszkancow/odbior-odpadow-gminy"

# Municipality name -> PDF slug ("harmonogram-<slug>-<year>.pdf").
_MUNICIPALITIES = {
    "Miasto Kraśnik": "miasto-krasnik",
    "Gmina Kraśnik": "g-krasnik",
    "Dzierzkowice": "dzierzkowice",
    "Gościeradów": "goscieradow",
    "Trzydnik Duży": "trzydnik-duzy",
    "Wilkołaz": "wilkolaz",
    "Strzyżewice": "strzyzewice",
    "Urzędów": "urzedow",
}

_TYPES = {
    "ZMIESZANE": wt.GENERAL_WASTE,
    "BIO": wt.ORGANIC,
    "ODPADY ZIELONE": wt.GARDEN_WASTE,
    "Metale i Tworzywa Sztuczne": wt.RECYCLABLES,
    "Papier": wt.PAPER,
    "Szkło": wt.GLASS,
    "POPIÓŁ": wt.OTHER,
    "GABARYTY": wt.BULKY_WASTE,
}
# Label lines as printed, lower-cased (the recyclables label wraps onto
# two lines, "Metale i" / "tworzywa sztuczne", worded slightly differently
# per municipality).
_LABELS = {
    "zmieszane": "ZMIESZANE",
    "bio": "BIO",
    "odpady zielone": "ODPADY ZIELONE",
    "papier": "Papier",
    "szkło": "Szkło",
    "popiół": "POPIÓŁ",
    "gabaryty": "GABARYTY",
}
_RECYCLABLES_LABEL = re.compile(r"(metale( i)?|tworzywa|sztuczne)( |$)")


def _label(text: str) -> str | None:
    text = re.sub(r"\s+", " ", text).strip().lower()
    if text in _LABELS:
        return _LABELS[text]
    if _RECYCLABLES_LABEL.match(text):
        return "Metale i Tworzywa Sztuczne"
    return None


def _schedule_pattern(municipality: str = "", **_: Any) -> str:
    """The configured municipality's detached-house PDFs, year in group 1."""
    slug = lookups.resolve(
        _MUNICIPALITIES,
        municipality,
        argument="municipality",
        normalize=lookups.normalize_loose,
    )
    return rf"harmonogram-{re.escape(slug)}-(20\d\d)\.pdf$"


def _streets(side_text: str) -> list[str]:
    """The area's places: a comma-separated list, or one place per line."""
    lines = side_text.splitlines()
    if any("," in line for line in lines):
        names = " ".join(lines).split(",")
    else:
        names = lines
    return [
        re.sub(r"^\d+\s+", "", re.sub(r"\s+", " ", name).strip())
        for name in names
        if name.strip()
    ]


def _select(
    blocks: list[preprocessors.GridBlock], source: Any = None
) -> list[tuple[datetime.date, str]]:
    """The configured street's rows, merged across the yearly PDFs.

    Once next year's PDF is linked both are read, so the rest of this year is
    not lost; within one PDF the first block listing the street wins.
    """
    wanted = lookups.normalize_loose(source.params["street"])
    names: set[str] = set()
    rows: dict[int, list[tuple[datetime.date, str]]] = {}
    for block in blocks:
        streets = _streets(block.side_text)
        names.update(streets)
        if block.year not in rows and any(
            lookups.normalize_loose(name) == wanted for name in streets
        ):
            rows[block.year] = block.rows
    if not rows:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", source.params["street"], sorted(names)
        )
    return [row for year in sorted(rows) for row in rows[year]]


@final
class Source(BaseSource):
    TITLE = "Ekoland Polska (Kraśnik area)"
    DESCRIPTION = (
        "Source for Ekoland Polska waste collection in the Kraśnik area, Poland."
    )
    URL = "https://www.ekolandpolska.com.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.OTHER,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Miasto Kraśnik, Lubelska": {
            "municipality": "Miasto Kraśnik",
            "street": "Lubelska",
        },
        "Miasto Kraśnik, Urzędowska": {
            "municipality": "Miasto Kraśnik",
            "street": "Urzędowska",
        },
        "Gmina Kraśnik, Lasy": {"municipality": "Gmina Kraśnik", "street": "Lasy"},
        "Dzierzkowice, Dębina": {"municipality": "Dzierzkowice", "street": "Dębina"},
        "Wilkołaz, Ostrów": {"municipality": "Wilkołaz", "street": "Ostrów"},
        "Strzyżewice, Bystrzyca Stara": {
            "municipality": "Strzyżewice",
            "street": "Bystrzyca Stara",
        },
        "Urzędów, Bęczyn": {"municipality": "Urzędów", "street": "Bęczyn"},
    }

    PARAMS = (
        municipality("municipality"),
        street("street"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality ('Miasto Kraśnik', 'Gmina Kraśnik', "
            "'Dzierzkowice', 'Gościeradów', 'Trzydnik Duży', 'Wilkołaz', "
            "'Strzyżewice' or 'Urzędów') and "
            "your street or village as printed in the schedule PDF linked on "
            "https://www.ekolandpolska.com.pl/dla-mieszkancow/odbior-odpadow-gminy "
            "(e.g. 'Lubelska' or 'Lasy'). Accents and case are ignored. Only detached "
            "houses (zabudowa jednorodzinna) are supported."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL,
            pick=retrievers.yearly_links(_schedule_pattern),
            # About one request in six gets a "One moment, please..."
            # interstitial without the download list, which reloads itself
            # after 5 s. An immediate repeat gets it again; one after 5 s gets
            # the page about half the time, so ask up to three times.
            retry_if=lambda response: "harmonogram-" not in response.text,
            retries=3,
            retry_delay=5,
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(min_words=200),
        then=preprocessors.PdfRoundMonthGrid(
            labels=_label,
            block_start="ZMIESZANE",
            # "od 01.01.2026" or "OD 2026.01.01"
            year_pattern=r"(?i)OD\s*(?:01\.01\.)?(20\d\d)",
            side_margin=150,
        ),
    )
    preprocess = staticmethod(_select)
    transform = ICSTransformer(type_value_map=_TYPES)
