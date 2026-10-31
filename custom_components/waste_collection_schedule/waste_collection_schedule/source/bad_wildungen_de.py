"""Stadt Bad Wildungen (Hesse), Germany.

The city publishes one calendar PDF per year, linked from its waste page. It
holds a twelve-month grid (one column per month, one row per day, each day
cell listing the collection tours of that day) and a street directory that
assigns every street or Stadtteil one tour per waste type.

The tour letters are disjoint per type (residual waste A-H, organic waste I-M
and J1, paper N-U, packaging 1-6 or "3+4"), so neither colour nor position
inside a cell is needed to tell the types apart. The calendar is read from
positioned words: a day cell starts at its printed weekday and day number,
every printed day is checked against its weekday, and the "J1" organic tour is
told apart from "J" plus packaging tour 1 by its digit sitting right next to
the letter. A "Keine Abfuhr <tour>" note cancels that tour on its day.
"""

import datetime
import itertools
import re
import unicodedata
from collections.abc import Iterable
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import parsers, recurrence, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer

_WASTE_PAGE = (
    "https://www.bad-wildungen.de/stadtverwaltung/was-erledige-ich-wo/"
    "abfallbeseitigung/"
)

_RESIDUAL = "Restmüll"
_ORGANIC = "Biomüll"
_PAPER = "Altpapier"
_PACKAGING = "Gelbe Tonne"

#: A street directory entry: its name, then one tour per waste type.
_ENTRY_RE = re.compile(
    r"^(?P<name>.*?)\s*(?<!\S)(?P<residual>[A-H])\s+(?P<organic>J\s?1|[I-M])"
    r"\s+(?P<paper>[N-U])\s+(?P<packaging>3\+4|[1-6])$"
)
_CODE_RE = re.compile(r"^(?:[A-U]|J1|[1-6]|3\+4)$")
_YEAR_RE = re.compile(r"Abfallkalender\s+(20\d\d)")


class _Tours(NamedTuple):
    residual: str
    organic: str
    paper: str
    packaging: str


def _name_key(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold().replace("ß", "ss")
    text = re.sub(r"str\.", "strasse", text)
    return re.sub(r"[^0-9a-zäöü]", "", text)


def _expect(condition: bool, detail: str, source: "BaseSource | None") -> None:
    response_shape.expect(
        condition, source_name=response_shape.source_name(source), detail=detail
    )


def _rows(
    words: list[parsers.PdfTextFragment], tolerance: float
) -> list[list[parsers.PdfTextFragment]]:
    """Words grouped into lines (top to bottom), each sorted left to right."""
    lines: list[list[parsers.PdfTextFragment]] = []
    for word in sorted(words, key=lambda w: -w.y):
        if lines and abs(lines[-1][0].y - word.y) <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])
    return [sorted(line, key=lambda w: w.x) for line in lines]


def _directory(
    layout: parsers.PdfWordLayout, source: "BaseSource | None"
) -> dict[str, tuple[str, _Tours]]:
    """Normalised name -> (printed name, tours) from the street directory.

    The directory prints five column groups headed "Straßenname" (four) and
    "Stadtteile". A name printed over two lines ("Brunnenstraße" / "Hsnr.:
    59, ...") or with its tours on the line below joins the tours line nearest
    to it; an "einschl. <street>" remark is dropped, as that street has its own
    entry with the same tours.
    """
    entries: dict[str, tuple[str, _Tours]] = {}
    pages = {
        w.page for w in layout.words if w.text in ("Straßenname", "Straßenverzeichnis")
    }
    for page in sorted(pages):
        words = [w for w in layout.words if w.page == page]
        headers = sorted(
            (w for w in words if w.text in ("Straßenname", "Stadtteile")),
            key=lambda w: w.x,
        )
        if len(headers) < 2:
            continue
        header_y = min(w.y for w in headers)
        starts = [w.x - 25 for w in headers]
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else float("inf")
            group = [w for w in words if start <= w.x < end and w.y < header_y - 2]
            coded: list[tuple[float, str, _Tours]] = []
            loose: list[tuple[float, str]] = []
            for line in _rows(group, 2.0):
                text = " ".join(w.text for w in line)
                if match := _ENTRY_RE.match(text):
                    tours = _Tours(
                        match["residual"],
                        match["organic"].replace(" ", ""),
                        match["paper"],
                        match["packaging"],
                    )
                    coded.append((line[0].y, match["name"], tours))
                else:
                    loose.append((line[0].y, text))
            parts: dict[int, list[tuple[float, str]]] = {
                i: [(y, name)] if name else [] for i, (y, name, _t) in enumerate(coded)
            }
            for y, text in loose:
                if not coded:
                    break
                nearest = min(range(len(coded)), key=lambda i: abs(coded[i][0] - y))
                if abs(coded[nearest][0] - y) <= 9:
                    parts[nearest].append((y, text))
            for i, (_y, _name, tours) in enumerate(coded):
                name = " ".join(t for _, t in sorted(parts[i], key=lambda p: -p[0]))
                name = re.sub(r"\s*einschl\..*$", "", name).strip()
                if name:
                    entries.setdefault(_name_key(name), (name, tours))
        if entries:
            # The PDF is exported as spreads: the other page holds the same
            # directory again, outside its visible area.
            break
    _expect(len(entries) >= 100, "street directory not found or changed", source)
    return entries


def _calendar(
    layout: parsers.PdfWordLayout, source: "BaseSource | None"
) -> Iterable[tuple[datetime.date, list[str]]]:
    """(date, tour codes) for every day cell of the twelve-month grid."""
    years = {
        int(m.group(1)) for line in layout.lines if (m := _YEAR_RE.search(line.text))
    }
    _expect(len(years) == 1, f"calendar year not found ({sorted(years)})", source)
    year = years.pop()

    for page in sorted({w.page for w in layout.words}):
        words = [w for w in layout.words if w.page == page]
        headings = [
            [(w, n) for w in line if (n := recurrence.month(w.text, "de")) is not None]
            for line in _rows(words, 2.0)
        ]
        months = next((found for found in headings if len(found) >= 12), [])
        if not months:
            continue
        _expect(
            [n for _w, n in months] == list(range(1, 13)),
            "month header changed",
            source,
        )
        header_y = months[0][0].y
        grid = [w for w in words if w.y < header_y - 2]

        # A cell anchor: a printed weekday with its day number right after it.
        anchors: list[tuple[parsers.PdfTextFragment, datetime.date]] = []
        for line in _rows(grid, 2.0):
            for first, second in itertools.pairwise(line):
                weekday = recurrence.weekday(first.text, "de", abbreviated=True)
                if weekday is None or not second.text.isdigit():
                    continue
                if not 0 < second.x - first.x < 25:
                    continue
                month = next((n for w, n in months if w.x > first.x), months[-1][1])
                try:
                    day = datetime.date(year, month, int(second.text))
                except ValueError:
                    day = None
                if day is None or day.weekday() != weekday:
                    _expect(
                        False,
                        f"{first.text} {second.text} does not fit {month}/{year}",
                        source,
                    )
                    continue
                anchors.append((second, day))
        _expect(len(anchors) >= 365, f"only {len(anchors)} day cells", source)

        # Columns run from one month's weekday position to the next's.
        lefts = sorted(
            {round(min(a.x for a, d in anchors if d.month == m)) for m in range(1, 13)}
        )
        width = lefts[1] - lefts[0]
        cells: dict[datetime.date, list[parsers.PdfTextFragment]] = {}
        anchor_words = {id(a) for a, _d in anchors}
        for word in grid:
            if id(word) in anchor_words:
                continue
            column = [i for i, left in enumerate(lefts) if left - 22 <= word.x]
            if not column or word.x > lefts[-1] + width - 22:
                continue
            month = column[-1] + 1
            candidates = [(a, d) for a, d in anchors if d.month == month]
            anchor, day = min(candidates, key=lambda c: abs(c[0].y - word.y))
            if abs(anchor.y - word.y) <= 6:
                cells.setdefault(day, []).append(word)

        for day, cell in sorted(cells.items()):
            yield day, _cell_codes(cell)
        # The PDF is exported as spreads: the next page holds the same grid
        # again, outside its visible area.
        return


def _cell_codes(cell: list[parsers.PdfTextFragment]) -> list[str]:
    """The tours a day cell lists, without those a "Keine Abfuhr" note cancels."""
    codes: list[str] = []
    cancelled: list[str] = []
    for line in _rows(cell, 1.5):
        merged: list[tuple[str, float]] = []
        for word in line:
            if (
                word.text == "1"
                and merged
                and merged[-1][0] == "J"
                and word.x - merged[-1][1] < 10
            ):
                merged[-1] = ("J1", word.x)
            else:
                merged.append((word.text, word.x))
        target = codes
        for token, _x in merged:
            if token == "Abfuhr":
                target = cancelled
            elif _CODE_RE.match(token):
                target.append(token)
    return [code for code in codes if code not in cancelled]


def _collections(
    layouts: list[parsers.PdfWordLayout], source: BaseSource
) -> Iterable[tuple[datetime.date, str]]:
    layout = layouts[0]
    directory = _directory(layout, source)
    wanted = source.params["street"]
    entry = directory.get(_name_key(wanted))
    if entry is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", wanted, sorted(name for name, _tours in directory.values())
        )
    tours = entry[1]
    labels = {
        tours.residual: _RESIDUAL,
        tours.organic: _ORGANIC,
        tours.paper: _PAPER,
        tours.packaging: _PACKAGING,
    }
    for day, codes in _calendar(layout, source):
        for code in dict.fromkeys(codes):
            if code in labels:
                yield day, labels[code]


@final
class Source(BaseSource):
    TITLE = "Stadt Bad Wildungen"
    DESCRIPTION = "Source for Stadt Bad Wildungen, Germany."
    URL = "https://www.bad-wildungen.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]
    TEST_CASES: ClassVar[dict] = {
        "Reinhardshausen": {"street": "Reinhardshausen"},
        "Brunnenallee klein": {"street": "Brunnenallee klein"},
        "Wega": {"street": "Wega"},
    }
    PARAMS = (street(),)
    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your street or, outside the core town, your Stadtteil (e.g. "
            "Reinhardshausen) as printed in the street directory of the city's "
            "waste calendar (Abfallkalender PDF on bad-wildungen.de). Where a "
            "street is split by house numbers, use the entry with the numbers, "
            "e.g. 'Königsquellenweg 12, 14, 16'."
        ),
        "de": (
            "Straße oder, außerhalb der Kernstadt, Stadtteil (z. B. "
            "Reinhardshausen) so, wie sie im Straßenverzeichnis des "
            "Abfallkalenders (PDF auf bad-wildungen.de) stehen. Ist eine Straße "
            "nach Hausnummern aufgeteilt, den Eintrag mit den Hausnummern "
            "wählen, z. B. 'Königsquellenweg 12, 14, 16'."
        ),
    }

    retrieve = retrievers.PdfLinkRetriever(
        index_url=_WASTE_PAGE, pattern=r"abfallkalender-(20\d\d)"
    )
    parse = parsers.PdfWordLayoutParser(min_words=1000, reading_order=False)
    preprocess = staticmethod(_collections)
    transform = ICSTransformer(
        type_value_map={
            _RESIDUAL: wt.GENERAL_WASTE,
            _ORGANIC: wt.ORGANIC,
            _PAPER: wt.PAPER,
            _PACKAGING: wt.RECYCLABLES,
        }
    )
