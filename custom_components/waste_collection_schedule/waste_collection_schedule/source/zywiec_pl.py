"""Miasto Żywiec, Poland.

The city publishes a half-yearly schedule PDF (collection by PUK EMPOL) on
https://zywiec.pl/harmonogram-wywozu-smieci. Each region ("rejon", I-XX) has a
row block: the region's streets on the left, then the rows S (selective), Z
(mixed), B (bio) and P (ash) in the "Termin" column, and one column of
collection days per month. The month names are printed vertically, so pdfminer
yields them as one-letter words stacked in the month's column; they are joined
bottom-up to recover the month and its x position.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import (
    config_params,
    lookups,
    parsers,
    recurrence,
    response_shape,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

SELECTIVE = "Tworzywa sztuczne, szkło, papier"
MIXED = "Odpady zmieszane"
BIO = "Bioodpady"
ASH = "Popiół"

_ROW_LABELS = {"S": SELECTIVE, "Z": MIXED, "B": BIO, "P": ASH}

_REGIONS = {f"Rejon {roman}": roman for roman in map(recurrence.to_roman, range(1, 21))}

_REGION_RE = re.compile(r"REJON\s+([IVXL]+)\b", re.IGNORECASE)
_DAYS_RE = re.compile(r"\d{1,2}(?:,\d{0,2})*")

# Day numbers of a row sit within this distance (points) of its S/Z/B/P label;
# rows are about 13 points apart.
_ROW_TOLERANCE = 6.0


def _month_columns(
    words: list[parsers.PdfTextFragment], top: float
) -> dict[int, float]:
    """Map month number to the x centre of its column on one page.

    The vertical month names arrive as single letters sharing one x, ordered
    bottom-up; only letters above the first table row (``top``) are used.
    """
    stacks: dict[int, list[parsers.PdfTextFragment]] = {}
    for word in words:
        if word.y > top + 8 and len(word.text) == 1 and word.text.isalpha():
            stacks.setdefault(round(word.x), []).append(word)
    columns: dict[int, float] = {}
    for x, letters in stacks.items():
        name = "".join(w.text for w in sorted(letters, key=lambda w: w.y))
        month = recurrence.month(name)
        if month is not None:
            columns[month] = float(x)
    return columns


def _rows(
    layouts: list[parsers.PdfWordLayout], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    region = lookups.resolve(
        _REGIONS,
        source.params["region"] if source else "",
        argument="region",
    )
    name = response_shape.source_name(source)
    layout = layouts[0]

    heading = next(
        (
            line
            for line in layout.lines
            if (match := _REGION_RE.match(line.text.strip()))
            and match.group(1).upper() == region
        ),
        None,
    )
    response_shape.expect(
        heading is not None,
        source_name=name,
        detail=f"no REJON {region} in the schedule PDF",
        raw=str(layout.lines[:20]),
    )
    if heading is None:
        return
    words = [word for word in layout.words if word.page == heading.page]
    lines = [line for line in layout.lines if line.page == heading.page]

    year_match = re.search(r"w roku (\d{4})", " ".join(line.text for line in lines))
    year = int(year_match.group(1)) if year_match else datetime.date.today().year

    # The S/Z/B/P labels form one narrow column right of the street lists.
    labels = [w for w in words if w.text in _ROW_LABELS and w.x > heading.x]
    response_shape.expect(
        len(labels) >= 4,
        source_name=name,
        detail=f"no S/Z/B/P rows on the page of REJON {region}",
        raw=str(lines[:20]),
    )
    if len(labels) < 4:
        return
    label_x = min(w.x for w in labels)
    labels = sorted((w for w in labels if abs(w.x - label_x) < 5), key=lambda w: -w.y)

    # Region blocks start at each S row; the heading belongs to the block whose
    # vertical span (S row to the next block) is nearest to it.
    starts = [i for i, w in enumerate(labels) if w.text == "S"]
    blocks = [
        labels[start : (starts[n + 1] if n + 1 < len(starts) else len(labels))]
        for n, start in enumerate(starts)
    ]

    def distance(block: list[parsers.PdfTextFragment]) -> float:
        top, bottom = block[0].y, block[-1].y
        if bottom <= heading.y <= top:
            return 0.0
        return min(abs(heading.y - top), abs(heading.y - bottom))

    block = min(blocks, key=distance)
    response_shape.expect(
        distance(block) < _ROW_TOLERANCE * 3,
        source_name=name,
        detail=f"no row block next to REJON {region}",
        raw=heading.text,
    )

    columns = _month_columns(words, top=labels[0].y)
    response_shape.expect(
        len(columns) >= 6,
        source_name=name,
        detail="month header not found",
        raw=str(sorted(columns)),
    )
    if not columns:
        return
    centres = sorted(columns.items(), key=lambda item: item[1])
    spacing = (centres[-1][1] - centres[0][1]) / max(len(centres) - 1, 1)

    for word in words:
        if word.x <= label_x + 8 or not _DAYS_RE.fullmatch(word.text):
            continue
        row = min(block, key=lambda label: abs(label.y - word.y))
        if abs(row.y - word.y) > _ROW_TOLERANCE:
            continue
        month, centre = min(centres, key=lambda item: abs(item[1] - word.x))
        if abs(centre - word.x) > spacing * 0.6:
            continue
        for day in re.findall(r"\d+", word.text):
            try:
                yield datetime.date(year, month, int(day)), _ROW_LABELS[row.text]
            except ValueError:
                continue


@final
class Source(BaseSource):
    TITLE = "Miasto Żywiec"
    DESCRIPTION = "Source for Miasto Żywiec waste collection schedule (Poland)"
    URL = "https://zywiec.pl/harmonogram-wywozu-smieci"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rejon V": {"region": "Rejon V"},
        "Rejon XI": {"region": "Rejon XI"},
    }

    PARAMS = (config_params.dropdown("region", list(_REGIONS), label="Region"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your collection region (rejon). The schedule PDF linked on "
            "https://zywiec.pl/harmonogram-wywozu-smieci lists the streets of "
            "each region next to its dates. Streets marked with * changed "
            "region in the current schedule, so check your region whenever a "
            "new half-year schedule is published."
        ),
    }

    retrieve = PdfLinkRetriever(
        index_url="https://zywiec.pl/harmonogram-wywozu-smieci",
        pattern=r"harmonogram[^/]*\.pdf",
        select="first",
    )
    parse = parsers.PdfWordLayoutParser(min_words=500)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            SELECTIVE: wt.RECYCLABLES,
            MIXED: wt.GENERAL_WASTE,
            BIO: wt.ORGANIC,
            ASH: wt.OTHER,
        }
    )
