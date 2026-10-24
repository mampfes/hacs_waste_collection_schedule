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
whose rows name a waste type followed by that month's days ("5, 19"). Empty
cells (seasonal rounds) are simply missing, so days are assigned to a month by
the x position of their word, not by their order in the row.
"""

import datetime
import itertools
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, parsers, recurrence, retrievers
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


def _blocks(
    layouts: list[parsers.PdfWordLayout], _source: Any = None
) -> list[dict[str, Any]]:
    """Split the PDF into area blocks: their streets and dated rows."""
    blocks: list[dict[str, Any]] = []
    for layout in layouts:
        year_match = re.search(
            r"OD\s*01\.01\.(20\d\d)", " ".join(f.text for f in layout.lines), re.I
        )
        if not year_match:
            raise ValueError("Ekoland: schedule year not found")
        year = int(year_match.group(1))
        named = [
            (w, month)
            for w in layout.words
            if (month := recurrence.month(w.text)) is not None
        ]
        # The header is the topmost row of month names; a street such as
        # "3 Maja" (genitive of May) further down must not count.
        header_y = max((w.y for w, _ in named), default=0.0)
        months = [(w.x, month) for w, month in named if abs(w.y - header_y) < 2]
        if len(months) != 12:
            raise ValueError("Ekoland: month header not found")
        first_month_x = min(x for x, _ in months)
        labels = sorted(
            (
                (line.y, label)
                for line in layout.lines
                if line.y < header_y and (label := _label(line.text))
            ),
            reverse=True,
        )
        starts = [y for y, label in labels if label == "ZMIESZANE"]
        bounds = [*starts, float("-inf")]
        first = len(blocks)
        for top, bottom in itertools.pairwise(bounds):
            streets = " ".join(
                line.text
                for line in sorted(layout.lines, key=lambda f: -f.y)
                if bottom + 8 < line.y <= min(top + 15, header_y - 5)
                and line.x < first_month_x - 150
                and not re.fullmatch(r"\d+", line.text)
            )
            blocks.append(
                {
                    "year": year,
                    "streets": [
                        re.sub(r"^\d+\s+", "", re.sub(r"\s+", " ", name).strip())
                        for name in streets.split(",")
                        if name.strip()
                    ],
                    "rows": [],
                }
            )
        # Each day belongs to the nearest label row (the recyclables label
        # wraps around its days), and that row's block.
        for word in layout.words:
            day = word.text.strip(",")
            if not (
                day.isdigit() and word.x > first_month_x - 25 and word.y < header_y - 5
            ):
                continue
            label_y, label = min(labels, key=lambda item: abs(item[0] - word.y))
            if abs(label_y - word.y) > 12:
                continue
            index = first + sum(1 for y in starts if y >= label_y - 1) - 1
            _, month = min(months, key=lambda item: abs(item[0] - word.x))
            blocks[index]["rows"].append((datetime.date(year, month, int(day)), label))
    return blocks


def _select(
    blocks: list[dict[str, Any]], source: Any = None
) -> list[tuple[datetime.date, str]]:
    """The configured street's rows, merged across the yearly PDFs.

    Once next year's PDF is linked both are read, so the rest of this year is
    not lost; within one PDF the first block listing the street wins.
    """
    wanted = lookups.normalize_loose(source.params["street"])
    names: set[str] = set()
    rows: dict[int, list[tuple[datetime.date, str]]] = {}
    for block in blocks:
        names.update(block["streets"])
        if block["year"] not in rows and any(
            lookups.normalize_loose(name) == wanted for name in block["streets"]
        ):
            rows[block["year"]] = block["rows"]
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
    }

    PARAMS = (
        municipality("municipality"),
        street("street"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality ('Miasto Kraśnik', 'Gmina Kraśnik', "
            "'Dzierzkowice', 'Gościeradów', 'Trzydnik Duży' or 'Wilkołaz') and "
            "your street or village as printed in the schedule PDF linked on "
            "https://www.ekolandpolska.com.pl/dla-mieszkancow/odbior-odpadow-gminy "
            "(e.g. 'Lubelska' or 'Lasy'). Accents and case are ignored. Only detached "
            "houses (zabudowa jednorodzinna) are supported."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX_URL, pick=retrievers.yearly_links(_schedule_pattern)
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(min_words=200), then=_blocks
    )
    preprocess = staticmethod(_select)
    transform = ICSTransformer(type_value_map=_TYPES)
