"""Pipeline components for ELWOZ ECO household calendar PDFs.

ELWOZ ECO (elwozeco.pl) publishes one PDF per sector of a municipality. Each
page is one village group for a twelve-month span (April to March): three
months across and four down, day numbers as text, and the collection type as
the cell's fill colour. A run of days of the same type is often one rectangle
rather than one per day. The legend at the foot of the page names the colours.

:func:`residential_pdfs` is the ``pick`` for the schedule index (household
calendars linked under one municipality heading, business and seasonal links
left out). :class:`PageRecords` reads a PDF into one
:class:`AreaDay` per coloured cell, and :class:`ForDistrict` keeps the village
or street the user named. Every day number is checked against the calendar
(it must exist and fall on the weekday column it is printed in) so a shifted
grid fails loudly instead of returning the wrong dates.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import lookups, response_shape
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import PdfWordLayout

#: Labels, in legend order. The source's transformer maps them to waste types.
MIXED = "Zmieszane odpady komunalne"
RECYCLING = "Metale i tworzywa sztuczne"
GLASS = "Szkło"
PAPER = "Papier"
BIO = "Odpady biodegradowalne"

# Link text (normalised) of calendars that are not household rounds.
_NON_HOUSEHOLD = ("firm", "domki", "letnisk", "pensjonat", "informacj", "wspolnot")

_MONTHS = {
    "styczen": 1,
    "luty": 2,
    "marzec": 3,
    "kwiecien": 4,
    "maj": 5,
    "czerwiec": 6,
    "lipiec": 7,
    "sierpien": 8,
    "wrzesien": 9,
    "pazdziernik": 10,
    "listopad": 11,
    "grudzien": 12,
}
_WEEKDAYS = {"pn": 0, "wt": 1, "sr": 2, "cz": 3, "pt": 4, "sb": 5, "nd": 6}
_LEGEND = (
    ("zmieszane", MIXED),
    ("tworzywa", RECYCLING),
    ("szklo", GLASS),
    ("papier", PAPER),
    ("biodegrad", BIO),
)
# Header lines that are not the village list. Matched against normalised text.
_BOILERPLATE = (
    "harmonogram",
    "zmieszanych",
    "segregowanych",
    "na terenie",
    "nieruchomosci",
    "legenda",
    "pojemnik",
)
_RANGE_RE = re.compile(r"(\w+)\s+(20\d{2})\s*[-–—]\s*(\w+)\s+(20\d{2})", re.UNICODE)
# A legend swatch and a calendar cell are both small filled rectangles. Cells
# of one colour are often merged across the week, so a cell may be much wider
# than a swatch, but neither is a hairline rule or a page-sized band.
_CELL_WIDTH = (10.0, 180.0)
_CELL_HEIGHT = (8.0, 36.0)
_SWATCH_WIDTH = (12.0, 40.0)
_SWATCH_HEIGHT = (8.0, 20.0)
# The legend blue and the cell blue differ by about 0.2 in one channel.
_COLOUR_TOLERANCE = 0.30
# Weekday headers of one month-row share a y; the next row is ~110 pt lower.
_HEADER_Y_TOLERANCE = 5.0
# Days sit just below their weekday header and stop short of the next month.
_DAY_BELOW = (4.0, 102.0)


class AreaDay(NamedTuple):
    """One coloured collection day and the villages that share its page."""

    area: str
    places: tuple[str, ...]
    date: date
    label: str


def residential_pdfs(municipality: str) -> Callable[..., list[str]]:
    """``pick``: household calendar PDFs linked under ``municipality``.

    The index page (``/harmonogram/``) has one ``h3`` per municipality and the
    PDF buttons that follow it until the next heading. Business (``Firmy``),
    holiday-home and information links are not household rounds.
    """

    wanted = lookups.normalize_loose(municipality)

    def pick(response: Any, *_keys: Any, **_params: Any) -> list[str]:
        soup = BeautifulSoup(response.text, "html.parser")
        heading = next(
            (
                tag
                for tag in soup.find_all("h3")
                if lookups.normalize_loose(tag.get_text(" ", strip=True)) == wanted
            ),
            None,
        )
        if heading is None:
            raise ValueError(
                f"no {municipality!r} heading on {response.url}; "
                "the schedule page changed"
            )
        urls: list[str] = []
        for tag in heading.find_all_next():
            if tag.name in {"h2", "h3"}:
                break
            if tag.name != "a" or not tag.get("href"):
                continue
            href = str(tag["href"])
            if not href.lower().split("?", 1)[0].endswith(".pdf"):
                continue
            label = lookups.normalize_loose(tag.get_text(" ", strip=True))
            first = label.split(" ", 1)[0]
            if first == "lt" or any(skip in label for skip in _NON_HOUSEHOLD):
                continue
            urls.append(urljoin(str(response.url), href))
        unique = list(dict.fromkeys(urls))
        if not unique:
            raise ValueError(
                f"no household calendar PDF linked under {municipality} "
                f"on {response.url}"
            )
        return unique

    return pick


def _rgb(colour: tuple[float, ...] | None) -> tuple[float, float, float] | None:
    if colour is None:
        return None
    if len(colour) == 1:
        value = float(colour[0])
        return (value, value, value)
    if len(colour) == 3:
        return (float(colour[0]), float(colour[1]), float(colour[2]))
    return None


def _is_white(rgb: tuple[float, float, float]) -> bool:
    return min(rgb) >= 0.90


def _is_neutral(rgb: tuple[float, float, float]) -> bool:
    """Grey page furniture, not a legend colour. Black is a real fill."""
    return max(rgb) - min(rgb) < 0.08 and 0.15 < max(rgb) < 0.92


def _nearest(
    rgb: tuple[float, float, float],
    palette: dict[tuple[float, float, float], str],
) -> str | None:
    best: str | None = None
    best_distance = _COLOUR_TOLERANCE + 1
    for known, label in palette.items():
        distance = (
            sum((left - right) ** 2 for left, right in zip(rgb, known, strict=True))
            ** 0.5
        )
        if distance < best_distance:
            best, best_distance = label, distance
    return best if best_distance <= _COLOUR_TOLERANCE else None


# "BANINO 2" / "DĄBROWA 7A-H": the word in front of the house-number suffix.
_ZONE_WORD_RE = re.compile(r"^([^\d\s]+)\s+\d")
# A page label the PDF prints as its own heading (``ŻUKOWO 1``, ``WIELORODZINNE``),
# as opposed to a street that happens to contain a digit.
_ZONE_LABEL_RE = re.compile(
    r"^(?:banino \d+|zukowo \d+|dabrowa \d|wielorodzinne|otomino)\b"
)
_HOUSE_NUMBER_RE = re.compile(r"\d+[A-Za-z]?(?:/\d+[A-Za-z]?)?")


def _join_heading(lines: list[str]) -> str:
    """Join the heading lines of one page into the list they were set as.

    A line break is a wrap, not a new place, while a parenthesis is still
    open (``Gdańska (od nr 42 … numery / parzyste)``) or when a comma already
    ended the line. A single word on either side of the break is a wrapped
    name (``Makuszyńskiego / Kornela``). Any other break is a new place that
    was printed without a separating comma.
    """
    joined = ""
    depth = 0
    for line in lines:
        text = re.sub(r"\s+", " ", line).strip()
        if not text:
            continue
        if not joined:
            joined = text
        elif depth > 0 or joined.endswith(",") or _wrapped_name(joined, text):
            joined = f"{joined} {text}"
        else:
            joined = f"{joined}, {text}"
        depth = max(0, depth + text.count("(") - text.count(")"))
    return joined


def _wrapped_name(previous: str, line: str) -> bool:
    tail = previous.rsplit(",", 1)[-1].strip()
    head = line.split(",", 1)[0].split("(", 1)[0].strip()
    return " " not in tail and " " not in head and head.isalpha()


def _split_places(text: str) -> list[str]:
    """Split on commas and ``oraz`` that are outside parentheses."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif depth == 0 and char == ",":
            parts.append("".join(buf))
            buf = []
            index += 1
            continue
        elif depth == 0 and (
            match := re.match(r"\s+oraz\s+", text[index:], re.IGNORECASE)
        ):
            parts.append("".join(buf))
            buf = []
            index += match.end()
            continue
        buf.append(char)
        index += 1
    parts.append("".join(buf))
    return parts


def _is_house_number(text: str) -> bool:
    return _HOUSE_NUMBER_RE.fullmatch(text) is not None


def _piece_names(part: str) -> list[str]:
    """One comma-separated piece, after the ``ulice:`` / ``ul.`` label."""
    part = re.sub(r"\s+", " ", part).strip(" .;:-")
    if not part:
        return []
    labelled = re.match(
        r"^(?:(?P<zone>.*?)\s+)?ulice:\s*(?P<street>.*)$", part, re.IGNORECASE
    )
    if labelled:
        names: list[str] = []
        zone = (labelled.group("zone") or "").strip(" .;:-")
        # "BANINO 1 ulice: …" is the zone. "Żukowo ulice: …" only repeats the
        # town already named by "ŻUKOWO 3" above the list.
        if zone and re.search(r"\d", zone):
            names.extend(_piece_names(zone))
        street = labelled.group("street").strip(" .;:-")
        if street:
            names.append(street)
        return names
    part = re.sub(r"^ul\.\s*", "", part, count=1, flags=re.IGNORECASE).strip(" .;:-")
    if not part:
        return []
    return [
        piece.strip(" .;:-")
        for piece in re.split(r"\s+\+\s+", part)
        if piece.strip(" .;:-") and not _is_house_number(piece.strip(" .;:-"))
    ]


def _tokens(text: str) -> list[str]:
    """Place names from a page heading (``A, B oraz C``, or a street list)."""
    names: list[str] = []
    seen: set[str] = set()
    for part in _split_places(text):
        for name in _piece_names(part):
            key = lookups.normalize_loose(name)
            if key and key not in seen:
                seen.add(key)
                names.append(name)
    return names


def _aliases(token: str) -> list[str]:
    """Shorter names that still mean this printed place.

    ``Gdańska (od nr 42 …)`` answers ``Gdańska``; ``ŻUKOWO 1`` answers
    ``Żukowo``; ``Przyjaźń ul. Kolejowa`` answers ``Kolejowa``. The caller
    treats a short name that hits more than one page as ambiguous.
    """
    found: list[str] = []

    def add(name: str) -> None:
        name = name.strip(" .;:-")
        if not name or _is_house_number(name):
            return
        if lookups.normalize_loose(name) == lookups.normalize_loose(token):
            return
        if name not in found:
            found.append(name)

    if "(" in token:
        add(token.split("(", 1)[0])
    if ":" in token:
        add(token.split(":", 1)[0])
    zone = _ZONE_WORD_RE.match(token)
    if zone:
        add(zone.group(1))
    street = re.search(r"\bul\.\s+(.+)$", token, re.IGNORECASE)
    if street:
        tail = street.group(1).strip()
        add(tail)
        tail_zone = _ZONE_WORD_RE.match(tail)
        if tail_zone:
            add(tail_zone.group(1))
    avenue = re.match(r"^al\.\s+(.+)$", token, re.IGNORECASE)
    if avenue:
        tail = avenue.group(1).strip()
        add(tail)
        tail_zone = _ZONE_WORD_RE.match(tail)
        if tail_zone:
            add(tail_zone.group(1))
    return found


def _is_zone_label(place: str) -> bool:
    if ":" in place or "(" in place:
        return False
    return _ZONE_LABEL_RE.match(lookups.normalize_loose(place)) is not None


def _round_trip_label(
    area: str,
    display: str,
    places: tuple[str, ...],
    index: dict[str, dict[str, str]],
) -> str:
    """A value the user can submit to select this page and no other.

    Prefers the printed name when that spelling is already unique, then a
    short zone heading (``ŻUKOWO 1``, ``WIELORODZINNE``), then the full page
    heading.
    """
    if len(index.get(lookups.normalize_loose(display), {})) == 1:
        return display
    zones = [place for place in places if _is_zone_label(place)]
    if zones:
        return min(
            zones, key=lambda place: (len(place), lookups.normalize_loose(place))
        )
    return area


def _span(lines: list[Any], page: int, source_name: str) -> tuple[int, int, int, int]:
    """``(start_month, start_year, end_month, end_year)`` from the page title."""
    for line in lines:
        if line.page != page:
            continue
        match = _RANGE_RE.search(line.text)
        if match is None:
            continue
        start = _MONTHS.get(lookups.normalize_loose(match.group(1)))
        end = _MONTHS.get(lookups.normalize_loose(match.group(3)))
        response_shape.expect(
            start is not None and end is not None,
            source_name=source_name,
            detail=f"unrecognised months in {line.text!r}",
            raw=line.text,
        )
        assert start is not None and end is not None
        return start, int(match.group(2)), end, int(match.group(4))
    response_shape.expect(
        False,
        source_name=source_name,
        detail=f"page {page + 1} has no 'month year - month year' title",
    )
    raise AssertionError


def _year_of(month: int, span: tuple[int, int, int, int]) -> int:
    start_month, start_year, _end_month, end_year = span
    if start_year == end_year or month >= start_month:
        return start_year
    return end_year


def _weekday_groups(words: list[Any], page: int) -> list[list[Any]]:
    """The seven weekday headers of each month, top to bottom, left to right."""
    headers = [
        word
        for word in words
        if word.page == page and lookups.normalize_loose(word.text) in _WEEKDAYS
    ]
    headers.sort(key=lambda word: -word.y)
    rows: list[list[Any]] = []
    for word in headers:
        if rows and abs(rows[-1][0].y - word.y) <= _HEADER_Y_TOLERANCE:
            rows[-1].append(word)
        else:
            rows.append([word])
    groups: list[list[Any]] = []
    for row in rows:
        row.sort(key=lambda word: word.x)
        if len(row) % 7 == 0:
            groups.extend(row[index : index + 7] for index in range(0, len(row), 7))
        else:
            groups.append(row)
    return groups


def _palette(
    layout: PdfWordLayout, page: int, source_name: str
) -> dict[tuple[float, float, float], str]:
    """Legend swatch colour to collection label, for this page."""
    lines = {
        label: line
        for line in layout.lines
        if line.page == page
        for keyword, label in _LEGEND
        if keyword in lookups.normalize_loose(line.text)
    }
    missing = [label for _keyword, label in _LEGEND if label not in lines]
    response_shape.expect(
        not missing,
        source_name=source_name,
        detail=f"page {page + 1} legend has no entry for {missing}",
        raw=" | ".join(line.text for line in layout.lines if line.page == page),
    )
    palette: dict[tuple[float, float, float], str] = {}
    for label in dict.fromkeys(label for _keyword, label in _LEGEND):
        line = lines[label]
        best: tuple[float, tuple[float, float, float]] | None = None
        for vector in layout.vectors:
            if vector.page != page or vector.fill_color is None:
                continue
            width, height = vector.x1 - vector.x0, vector.y1 - vector.y0
            if not (
                _SWATCH_WIDTH[0] <= width <= _SWATCH_WIDTH[1]
                and _SWATCH_HEIGHT[0] <= height <= _SWATCH_HEIGHT[1]
            ):
                continue
            rgb = _rgb(vector.fill_color)
            if rgb is None or _is_white(rgb):
                continue
            center_x = (vector.x0 + vector.x1) / 2
            center_y = (vector.y0 + vector.y1) / 2
            if center_x > line.x - 15 or abs(center_y - line.y) > 16:
                continue
            distance = abs(center_y - line.y)
            if best is None or distance < best[0]:
                best = (distance, rgb)
        response_shape.expect(
            best is not None,
            source_name=source_name,
            detail=f"page {page + 1} has no colour swatch for {label}",
            raw=line.text,
        )
        assert best is not None
        red, green, blue = best[1]
        palette[(round(red, 3), round(green, 3), round(blue, 3))] = label
    response_shape.expect(
        len(set(palette.values())) == len(_LEGEND),
        source_name=source_name,
        detail=f"page {page + 1} legend colours are not distinct: {palette}",
    )
    return palette


def _cell_label(
    layout: PdfWordLayout,
    page: int,
    x: float,
    y: float,
    palette: dict[tuple[float, float, float], str],
    source_name: str,
) -> str | None:
    """The legend label of the smallest coloured cell containing ``(x, y)``."""
    found: list[tuple[float, str | None, tuple[float, float, float]]] = []
    for vector in layout.vectors:
        if vector.page != page or vector.fill_color is None:
            continue
        width, height = vector.x1 - vector.x0, vector.y1 - vector.y0
        if not (
            _CELL_WIDTH[0] <= width <= _CELL_WIDTH[1]
            and _CELL_HEIGHT[0] <= height <= _CELL_HEIGHT[1]
        ):
            continue
        if not (vector.x0 - 0.8 <= x <= vector.x1 + 0.8):
            continue
        if not (vector.y0 - 0.8 <= y <= vector.y1 + 0.8):
            continue
        rgb = _rgb(vector.fill_color)
        if rgb is None or _is_white(rgb):
            continue
        found.append((width * height, _nearest(rgb, palette), rgb))
    labelled = [item for item in found if item[1] is not None]
    if labelled:
        labelled.sort(key=lambda item: item[0])
        return labelled[0][1]
    chromatic = [item for item in found if not _is_neutral(item[2])]
    if chromatic:
        red, green, blue = chromatic[0][2]
        response_shape.expect(
            False,
            source_name=source_name,
            detail=(
                f"page {page + 1} day cell at ({x:.0f},{y:.0f}) is filled "
                f"{red:.2f},{green:.2f},{blue:.2f}, which matches no legend colour"
            ),
        )
    return None


def _places(
    layout: PdfWordLayout, page: int, source_name: str
) -> tuple[str, tuple[str, ...]]:
    # The title repeats two month names ("KWIECIEŃ 2026 - MARZEC 2027") above
    # the village list, so the cutoff is the weekday headers, not every month
    # word. Calendar month titles sit just above those headers and are dropped
    # as month names below.
    header_ys = [
        word.y
        for word in layout.words
        if word.page == page and lookups.normalize_loose(word.text) in _WEEKDAYS
    ]
    response_shape.expect(
        bool(header_ys),
        source_name=source_name,
        detail=f"page {page + 1} has no weekday headers",
    )
    top = max(header_ys)
    texts: list[str] = []
    for line in sorted(
        (line for line in layout.lines if line.page == page and line.y > top + 4),
        key=lambda line: -line.y,
    ):
        normalised = lookups.normalize_loose(line.text)
        if _RANGE_RE.search(line.text) or any(
            part in normalised for part in _BOILERPLATE
        ):
            continue
        if normalised in _MONTHS or normalised in _WEEKDAYS:
            continue
        texts.append(line.text.strip())
    tokens = _tokens(_join_heading(texts))
    response_shape.expect(
        bool(tokens),
        source_name=source_name,
        detail=f"page {page + 1} has no village heading",
        raw=" | ".join(line.text for line in layout.lines if line.page == page),
    )
    return " ".join(texts), tuple(tokens)


def _page_records(layout: PdfWordLayout, page: int, source_name: str) -> list[AreaDay]:
    span = _span(layout.lines, page, source_name)
    start_month, start_year, end_month, end_year = span
    start = date(start_year, start_month, 1)
    if end_month == 12:
        end = date(end_year, 12, 31)
    else:
        end = date(end_year, end_month + 1, 1) - timedelta(days=1)
    expected = (end - start).days + 1

    groups = _weekday_groups(layout.words, page)
    response_shape.expect(
        len(groups) == 12 and all(len(group) == 7 for group in groups),
        source_name=source_name,
        detail=(
            f"page {page + 1} has {len(groups)} weekday rows, not 12 months "
            f"of 7 headers ({[len(group) for group in groups]})"
        ),
    )
    palette = _palette(layout, page, source_name)
    area, places = _places(layout, page, source_name)
    day_words = [
        word
        for word in layout.words
        if word.page == page and re.fullmatch(r"\d{1,2}", word.text)
    ]

    dated: dict[date, set[str]] = {}
    seen: set[date] = set()
    problems: list[str] = []
    for group in groups:
        header_y = sum(word.y for word in group) / len(group)
        x_min = min(word.x for word in group)
        x_max = max(word.x for word in group)
        columns = {
            _WEEKDAYS[lookups.normalize_loose(word.text)]: word.x for word in group
        }
        if set(columns) != set(_WEEKDAYS.values()):
            problems.append(
                f"page {page + 1} weekday header is "
                f"{[word.text for word in group]}, not Pn–Nd"
            )
            continue
        months = [
            word
            for word in layout.words
            if word.page == page
            and lookups.normalize_loose(word.text) in _MONTHS
            and x_min - 30 <= word.x <= x_max + 30
            and header_y < word.y < header_y + 40
        ]
        if len(months) != 1:
            problems.append(
                f"page {page + 1} y={header_y:.0f}: "
                f"{len(months)} month names above the weekday header"
            )
            continue
        month = _MONTHS[lookups.normalize_loose(months[0].text)]
        year = _year_of(month, span)
        for word in day_words:
            if not (x_min - 16 <= word.x <= x_max + 16):
                continue
            if not (header_y - _DAY_BELOW[1] <= word.y <= header_y - _DAY_BELOW[0]):
                continue
            weekday = min(columns, key=lambda key: abs(columns[key] - word.x))
            try:
                day = date(year, month, int(word.text))
            except ValueError:
                problems.append(
                    f"page {page + 1}: {word.text} is not a {year}-{month:02d} day"
                )
                continue
            if day.weekday() != weekday:
                problems.append(
                    f"page {page + 1}: {day.isoformat()} is printed in the "
                    f"{weekday} column"
                )
                continue
            if day in seen:
                problems.append(f"page {page + 1}: {day.isoformat()} printed twice")
                continue
            seen.add(day)
            label = _cell_label(layout, page, word.x, word.y, palette, source_name)
            if label is not None:
                dated.setdefault(day, set()).add(label)

    response_shape.expect(
        not problems,
        source_name=source_name,
        detail="; ".join(problems[:4]),
    )
    response_shape.expect(
        len(seen) == expected,
        source_name=source_name,
        detail=(
            f"page {page + 1} ({area}) has {len(seen)} days, "
            f"expected {expected} from {start.isoformat()} to {end.isoformat()}"
        ),
    )
    coloured = sum(len(labels) for labels in dated.values())
    response_shape.expect(
        coloured >= 10,
        source_name=source_name,
        detail=f"page {page + 1} ({area}) has only {coloured} coloured days",
    )
    return [
        AreaDay(area, places, day, label)
        for day, labels in sorted(dated.items())
        for label in sorted(labels)
    ]


class PageRecords:
    """Turn one ELWOZ ECO calendar PDF into :class:`AreaDay` rows.

    Used as ``parsers.EachResponse(PdfWordLayoutParser(...), then=PageRecords())``.
    """

    def __call__(
        self, layouts: Iterable[PdfWordLayout], source: BaseSource | None = None
    ) -> list[AreaDay]:
        name = response_shape.source_name(source)
        records: list[AreaDay] = []
        for layout in layouts:
            pages = sorted(
                {word.page for word in layout.words}
                | {line.page for line in layout.lines}
            )
            response_shape.expect(
                bool(pages),
                source_name=name,
                detail="the calendar PDF has no text",
            )
            for page in pages:
                records.extend(_page_records(layout, page, name))
        return records


class ForDistrict:
    """Keep the collections for the village or street named by ``argument``.

    A page heading lists every place that shares it. The value must match one
    printed name (case, accents and a leading ``ul.`` ignored). A parenthetical
    house-number range, a ``ŻUKOWO 1`` zone label and a ``ul.`` / ``Al.``
    prefix also match their short form. A short form printed on more than one
    page raises and lists those printed names.
    """

    def __init__(self, argument: str = "district") -> None:
        self.argument = argument

    def __call__(
        self, records: Iterable[AreaDay], source: BaseSource | None = None
    ) -> Iterable[tuple[date, str]]:
        if source is None:
            raise ValueError("ForDistrict needs the source")
        rows = list(records)
        value = source.params.get(self.argument)
        by_area: dict[str, tuple[str, ...]] = {}
        for row in rows:
            by_area.setdefault(row.area, row.places)
        # Normalised name -> page heading -> the printed name to suggest.
        index: dict[str, dict[str, str]] = defaultdict(dict)
        for area, places in by_area.items():
            for place in places:
                index[lookups.normalize_loose(place)].setdefault(area, place)
                for alias in _aliases(place):
                    index[lookups.normalize_loose(alias)].setdefault(area, place)
        known = sorted(
            {place for places in by_area.values() for place in places},
            key=lookups.normalize_loose,
        )
        if value in (None, ""):
            raise SourceArgumentNotFoundWithSuggestions(self.argument, value, known)
        wanted = lookups.normalize_loose(str(value))
        # A query that is a whole page heading selects that page, including a
        # page titled with one place ("Przyjaźń"). A name that is only part of
        # several headings stays ambiguous; the suggestions each select one page.
        headings = [area for area in by_area if lookups.normalize_loose(area) == wanted]
        matched = index.get(wanted, {})
        if len(headings) == 1:
            area = headings[0]
        elif not matched:
            raise SourceArgumentNotFoundWithSuggestions(self.argument, value, known)
        elif len(matched) > 1:
            suggestions = sorted(
                {
                    _round_trip_label(area, display, by_area[area], index)
                    for area, display in matched.items()
                },
                key=lookups.normalize_loose,
            )
            raise SourceArgAmbiguousWithSuggestions(self.argument, value, suggestions)
        else:
            area = next(iter(matched))
        seen: set[tuple[date, str]] = set()
        for row in rows:
            if row.area == area and (row.date, row.label) not in seen:
                seen.add((row.date, row.label))
                yield row.date, row.label
