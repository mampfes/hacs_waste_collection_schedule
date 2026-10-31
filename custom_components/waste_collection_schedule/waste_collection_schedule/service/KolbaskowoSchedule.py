"""Schedule PDFs for single-family housing in Gmina Kołbaskowo, Poland.

The municipality links one PDF per village (some villages split by street or
house-number range) from a stable index page. Each file is a Word table: a
column per month (November 2026 through December 2027 on the current run), a
row per waste round, and the days of that month in the cell. A ``*`` marks a
collection already moved off a holiday; the printed day is the collection day.

Plastik, Papier and Szkło share one cell. The horizontal borders between those
three label rows stop at the label column, so the date columns have a single
tall cell and the three rounds are collected on the same days.
``RuledTableParser`` only sees rules that span the whole table, which these
per-cell borders do not, and a uniform grid would also split that merged cell.
:func:`_table_cells` rebuilds each column from the border segments that
actually cross it.

:func:`schedule_links` and :func:`choose_schedule` resolve the configured
village (and optional street or house number) to the PDF URL. :class:`ScheduleParser`
yields ``(date, label)`` rows for an ``ICSTransformer``.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from io import BytesIO
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import lookups, recurrence, response_shape
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.PdfRuledTable import cell_text, collapse_edges

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Response

# A border is a filled rectangle thinner than this (PDF points) in one direction.
_THICKNESS = 3.0
# Shorter strokes are decorations, not table borders.
_MIN_RULE = 15.0
# Rules closer than this are one edge (a border drawn twice).
_EDGE = 3.0
# Vertical rules of adjacent rows abut; a gap under this still joins them into
# one table. The legend further down the page is much further away.
_ROW_GAP = 8.0
# A date cell must overlap a label row by more than a shared border.
_OVERLAP = 2.0

# Printed round name (accents and the trailing "*" dropped) -> label yielded
# to the transformer. Plastik and metal are one round.
_LABELS = {
    "zmieszane": "Zmieszane",
    "plastik metal": "Plastik, metal",
    "papier": "Papier",
    "szklo": "Szkło",
    "bio": "BIO",
    "gabaryty": "Gabaryty",
}
_HEADER_LABELS = frozenset({"odpady"})
_REQUIRED = (
    "Zmieszane",
    "Plastik, metal",
    "Papier",
    "Szkło",
    "BIO",
    "Gabaryty",
)

# "KURÓW (bez ...)" / "KURÓW ul. Na Klifie" / "BĘDARGOWO nr 50 - 57" /
# "tzw. MAŁE STOBNO ( STOBNO 52-54 U)": the place is the leading name.
_PLACE = re.compile(
    r"^(?:tzw\.\s*)?(?P<place>.+?)(?:\s+(?:bez|ul\.?|nr)\b|\s*\(|\s*$)",
    re.IGNORECASE,
)
_RANGE = re.compile(r"(\d+)\s*-\s*(\d+)")
_HOUSE_TOKEN = re.compile(r"\d+[A-Za-z]?")


class ScheduleLink(NamedTuple):
    """One schedule PDF as the index page prints it."""

    name: str
    url: str


class _Cell(NamedTuple):
    col: int
    text: str
    x0: float
    x1: float
    y0: float
    y1: float


def _walk(obj: Any) -> Any:
    yield obj
    if hasattr(obj, "__iter__"):
        for child in obj:
            yield from _walk(child)


def schedule_links(response: Response) -> list[ScheduleLink]:
    """The schedule PDFs linked from an index page, in page order."""
    soup = BeautifulSoup(response.text, "html.parser")
    tags = soup.select("a.file_add__name[href]")
    if not tags:
        tags = [
            tag
            for tag in soup.find_all("a", href=True)
            if "file_add/download" in str(tag["href"])
        ]
    found: dict[str, str] = {}
    base = getattr(response, "url", "") or ""
    for tag in tags:
        href = str(tag["href"])
        if not href.lower().split("?", 1)[0].endswith(".pdf"):
            continue
        name = " ".join(tag.get_text(" ", strip=True).split())
        if name:
            found.setdefault(urljoin(base, href), name)
    links = [ScheduleLink(name, url) for url, name in found.items()]
    response_shape.expect(
        bool(links),
        source_name="kolbaskowo_pl",
        detail="index page lists no schedule PDFs",
        raw=getattr(response, "text", "")[:500],
    )
    return links


def _place(name: str) -> str:
    match = _PLACE.match(name.strip())
    return match.group("place").strip() if match else name.strip()


def _qualifier(name: str) -> str:
    """The part of a link title after the place name (exclusions or a subset)."""
    match = _PLACE.match(name.strip())
    if not match:
        return ""
    return name.strip()[match.end("place") :].strip()


def _kind(qualifier: str) -> str:
    """``plain`` (the whole place), ``exclusion`` (only ``bez`` clauses) or
    ``inclusion`` (a street or house-number subset).

    Every current file is one of those three. A title that mixed an exclusion
    with a positive subset would need another look.
    """
    body = qualifier.strip().strip("() ")
    if not body:
        return "plain"
    if re.match(r"bez\b", body, flags=re.IGNORECASE):
        return "exclusion"
    return "inclusion"


def _house_numbers(text: str) -> set[str]:
    """House numbers a title mentions: ``50 - 57`` expands, ``32a`` stays."""
    found: set[str] = set()
    masked = list(text)
    for match in _RANGE.finditer(text):
        start, end = int(match.group(1)), int(match.group(2))
        if 0 < start <= end <= start + 400:
            found.update(str(number) for number in range(start, end + 1))
            for index in range(match.start(), match.end()):
                masked[index] = " "
    for match in _HOUSE_TOKEN.finditer("".join(masked)):
        found.add(lookups.normalize_loose(match.group(0)))
    return found


def _clean_street(street: str) -> str:
    return re.sub(r"^ul\s+", "", lookups.normalize_loose(street)).strip()


def _clean_house(house: str) -> str:
    return re.sub(r"^nr\s+", "", lookups.normalize_loose(house)).strip()


def _house_matches(house: str, numbers: set[str]) -> bool:
    if not numbers:
        return False
    wanted = _clean_house(house)
    if wanted in numbers:
        return True
    # "52U" for a range printed "52-54 U".
    suffix = re.fullmatch(r"(\d+)[a-z]", wanted)
    return bool(suffix and suffix.group(1) in numbers)


def _tokens_close(left: str, right: str) -> bool:
    """True when two tokens are equal or differ only by a Polish ending.

    ``Wędrowna`` on one file and ``Wędrownej`` on the other name one street.
    """
    if left == right:
        return True
    shared = 0
    for a, b in zip(left, right, strict=False):
        if a != b:
            break
        shared += 1
    short = min(len(left), len(right))
    return shared >= 6 and shared >= short - 2


def _street_in(street: str, text: str) -> bool:
    wanted = _clean_street(street)
    hay = lookups.normalize_loose(text)
    if not wanted:
        return False
    if re.search(rf"(?:^|\s){re.escape(wanted)}(?:\s|$)", hay):
        return True
    hay_tokens = hay.split()
    start = 0
    for token in wanted.split():
        found = False
        for index in range(start, len(hay_tokens)):
            if _tokens_close(token, hay_tokens[index]):
                start = index + 1
                found = True
                break
        if not found:
            return False
    return True


def _mentions(text: str, wanted: str) -> bool:
    return wanted != "" and re.search(rf"\b{re.escape(wanted)}\b", text) is not None


def _names(links: list[ScheduleLink]) -> list[str]:
    return sorted({link.name for link in links}, key=lookups.normalize_loose)


def _split_query(
    district: str, links: list[ScheduleLink]
) -> tuple[str, str | None, str | None]:
    """Split ``Kurów 1`` or ``Kurów Na Klifie`` into a place plus a refinement.

    Returns the place as the link prints it, and either a house number or a
    street. A district that already is a place name is returned unchanged.
    """
    wanted = lookups.normalize_loose(district)
    places: dict[str, str] = {}
    for link in links:
        places.setdefault(lookups.normalize_loose(_place(link.name)), _place(link.name))
    if wanted in places:
        return district, None, None
    best: tuple[int, str, str] | None = None
    for key, original in places.items():
        prefix = key + " "
        if wanted.startswith(prefix) and (best is None or len(key) > best[0]):
            best = (len(key), wanted[len(prefix) :], original)
    if best is None:
        return district, None, None
    _, rest, original = best
    if re.fullmatch(r"\d+[a-z]?", rest):
        return original, None, rest
    rest = re.sub(r"^ul\s+", "", rest).strip()
    return original, rest or None, None


def _positive(link: ScheduleLink, street: str | None, house: str | None) -> bool:
    """Whether an inclusion file (one street, or a house-number range) is the
    one the arguments ask for."""
    if _kind(_qualifier(link.name)) != "inclusion":
        return False
    qualifier = _qualifier(link.name)
    numbers = _house_numbers(qualifier)
    street_ok = _street_in(street, qualifier) if street else False
    house_ok = _house_matches(house, numbers) if house and numbers else False
    if street and house:
        return street_ok and house_ok if numbers else street_ok
    if street:
        return street_ok
    if house:
        return house_ok
    return False


def _default(link: ScheduleLink, street: str | None, house: str | None) -> bool:
    """Whether a whole-village file (or its ``bez`` remainder) covers this query."""
    qualifier = _qualifier(link.name)
    kind = _kind(qualifier)
    if kind == "inclusion":
        return False
    if kind == "exclusion":
        if street and _street_in(street, qualifier):
            return False
        if house and _house_matches(house, _house_numbers(qualifier)):
            return False
    return True


def choose_schedule(
    links: list[ScheduleLink],
    district: str,
    *,
    street: str | None = None,
    house_number: str | None = None,
) -> str:
    """The PDF URL for ``district``.

    A village typed on its own selects the file that covers the rest of the
    village (the plain name, or the one that only lists ``bez`` exclusions).
    ``street`` selects ``ul. ...`` files; ``house_number`` selects ``nr ...``
    ranges, including Małe Stobno when the number is 52-54. The full link
    title (``KURÓW ul. Na Klifie``) matches too.
    """
    street = street.strip() if isinstance(street, str) else None
    house = str(house_number).strip() if house_number not in (None, "") else None
    street = street or None
    house = house or None
    wanted = lookups.normalize_loose(district)

    # A pasted link title ("KURÓW ul. Na Klifie") wins only when no street or
    # house number was also given. "Stobno" is itself a whole link title, so
    # an exact match must not discard house 52-54 (Małe Stobno).
    if street is None and house is None:
        exact = [link for link in links if lookups.normalize_loose(link.name) == wanted]
        if len(exact) == 1:
            return exact[0].url
        if len(exact) > 1:
            raise SourceArgAmbiguousWithSuggestions("district", district, _names(exact))

    if street is None and house is None:
        district, split_street, split_house = _split_query(district, links)
        street = split_street
        house = split_house
        wanted = lookups.normalize_loose(district)

    candidates = [
        link for link in links if lookups.normalize_loose(_place(link.name)) == wanted
    ]
    if house:
        for link in links:
            if link in candidates:
                continue
            # "tzw. MAŁE STOBNO ( STOBNO 52-54 U)" is not the place Stobno, but
            # it is the schedule for those Stobno numbers.
            if _mentions(lookups.normalize_loose(link.name), wanted) and _positive(
                link, street, house
            ):
                candidates.append(link)
    if not candidates:
        close = [
            link
            for link in links
            if _mentions(lookups.normalize_loose(link.name), wanted)
        ]
        raise SourceArgumentNotFoundWithSuggestions(
            "district", district, _names(close or links)
        )

    positive = [link for link in candidates if _positive(link, street, house)]
    if len(positive) == 1:
        return positive[0].url
    if len(positive) > 1:
        argument = "street" if street else "house_number" if house else "district"
        value = street or house or district
        raise SourceArgAmbiguousWithSuggestions(argument, value, _names(positive))

    defaults = [link for link in candidates if _default(link, street, house)]
    if len(defaults) == 1:
        return defaults[0].url
    if len(defaults) > 1:
        raise SourceArgAmbiguousWithSuggestions("district", district, _names(defaults))
    if len(candidates) == 1 and street is None and house is None:
        return candidates[0].url

    argument = "street" if street else "house_number" if house else "district"
    value = street or house or district
    raise SourceArgumentNotFoundWithSuggestions(argument, value, _names(candidates))


def _table_cells(page: Any) -> list[_Cell]:
    """The schedule table's cells, one column's borders at a time.

    Date columns do not have the label column's extra horizontal rules, so a
    merged Plastik/Papier/Szkło cell stays one cell.
    """
    from pdfminer.layout import LTChar, LTCurve

    objects = list(_walk(page))
    curves = [obj for obj in objects if isinstance(obj, LTCurve)]
    vertical = [
        rule for rule in curves if rule.width < _THICKNESS and rule.height > _MIN_RULE
    ]
    horizontal = [
        rule for rule in curves if rule.height < _THICKNESS and rule.width > _MIN_RULE
    ]
    chars = [obj for obj in objects if isinstance(obj, LTChar)]
    bands: list[list[Any]] = []
    for segment in sorted(vertical, key=lambda rule: -rule.y1):
        for band in bands:
            y0 = min(rule.y0 for rule in band)
            y1 = max(rule.y1 for rule in band)
            gap = max(segment.y0, y0) - min(segment.y1, y1)
            if gap < _ROW_GAP:
                band.append(segment)
                break
        else:
            bands.append([segment])
    large = [band for band in bands if len(band) >= 10]
    if not large:
        return []
    # The schedule sits above the sorting-guide legend.
    band = max(large, key=lambda rules: max(rule.y1 for rule in rules))
    table_y0 = min(rule.y0 for rule in band)
    table_y1 = max(rule.y1 for rule in band)
    xs = collapse_edges([rule.x0 for rule in band] + [rule.x1 for rule in band], _EDGE)
    rules = [
        rule for rule in horizontal if table_y0 - _EDGE <= rule.y0 <= table_y1 + _EDGE
    ]
    cells: list[_Cell] = []
    column = 0
    for index in range(len(xs) - 1):
        x0, x1 = xs[index], xs[index + 1]
        if x1 - x0 < _MIN_RULE:
            continue
        ys = collapse_edges(
            [rule.y0 for rule in rules if rule.x1 > x0 + 1 and rule.x0 < x1 - 1],
            _EDGE,
        )
        for row in range(len(ys) - 1):
            bottom, top = ys[row], ys[row + 1]
            if top - bottom < _ROW_GAP:
                continue
            belonging = [
                char
                for char in chars
                if x0 <= (char.x0 + char.x1) / 2 < x1
                and bottom < (char.y0 + char.y1) / 2 <= top
            ]
            cells.append(_Cell(column, cell_text(belonging), x0, x1, bottom, top))
        column += 1
    return cells


def _label(text: str) -> str | None:
    key = lookups.normalize_loose(text.replace("*", ""))
    if not key or key in _HEADER_LABELS:
        return None
    return _LABELS.get(key)


def _header(text: str) -> tuple[int, int] | None:
    year = month = None
    for token in re.findall(r"[0-9A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż]+", text):
        if re.fullmatch(r"20\d\d", token):
            year = int(token)
        else:
            number = recurrence.month(token, locale="pl")
            if number:
                month = number
    if year and month:
        return year, month
    return None


def _overlaps(cell: _Cell, other: _Cell) -> bool:
    return min(cell.y1, other.y1) - max(cell.y0, other.y0) > _OVERLAP


def _rows_from_page(page: Any, source: BaseSource | None) -> list[tuple[date, str]]:
    cells = _table_cells(page)
    if not cells:
        return []
    by_col: dict[int, list[_Cell]] = defaultdict(list)
    for cell in cells:
        by_col[cell.col].append(cell)
    label_col = max(
        by_col,
        key=lambda col: sum(_label(cell.text) is not None for cell in by_col[col]),
    )
    labels = [cell for cell in by_col[label_col] if _label(cell.text)]
    unknown = [
        cell.text
        for cell in by_col[label_col]
        if cell.text.strip()
        and _label(cell.text) is None
        and _header(cell.text) is None
        and lookups.normalize_loose(cell.text.replace("*", "").strip(" :"))
        not in _HEADER_LABELS
    ]
    response_shape.expect(
        not unknown,
        source_name=response_shape.source_name(source),
        detail=f"unrecognised waste round(s) {unknown}",
        raw=str(unknown),
    )
    rows: list[tuple[date, str]] = []
    months = 0
    for column, column_cells in by_col.items():
        if column == label_col:
            continue
        header = max(column_cells, key=lambda cell: cell.y1)
        parsed = _header(header.text)
        if parsed is None:
            if any(re.search(r"\d", cell.text) for cell in column_cells):
                response_shape.expect(
                    False,
                    source_name=response_shape.source_name(source),
                    detail=f"month header not readable: {header.text!r}",
                    raw=header.text,
                )
            continue
        year, month = parsed
        months += 1
        for cell in column_cells:
            if cell is header:
                continue
            days = [
                int(number)
                for number in re.findall(r"(?<!\d)(\d{1,2})(?!\d)", cell.text)
            ]
            if not days:
                continue
            round_labels = [
                name
                for label in labels
                if _overlaps(cell, label) and (name := _label(label.text))
            ]
            response_shape.expect(
                bool(round_labels),
                source_name=response_shape.source_name(source),
                detail=(
                    f"dates {cell.text!r} in {month}/{year} do not fall in a "
                    "waste-round row"
                ),
                raw=cell.text,
            )
            for day in days:
                response_shape.expect(
                    1 <= day <= 31,
                    source_name=response_shape.source_name(source),
                    detail=f"day {day} is not a calendar day ({cell.text!r})",
                    raw=cell.text,
                )
                try:
                    when = date(year, month, day)
                except ValueError:
                    response_shape.expect(
                        False,
                        source_name=response_shape.source_name(source),
                        detail=f"{year}-{month:02d}-{day:02d} is not a real date",
                        raw=cell.text,
                    )
                    continue
                rows.extend((when, name) for name in round_labels)
    response_shape.expect(
        months >= 10,
        source_name=response_shape.source_name(source),
        detail=f"schedule table has {months} month columns, expected at least 10",
        raw=str(months),
    )
    return rows


class ScheduleParser:
    """Read a Kołbaskowo schedule PDF into ``(date, round label)`` rows."""

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pdfminer.high_level import extract_pages

        rows: list[tuple[date, str]] = []
        for page in extract_pages(BytesIO(response.content)):
            rows.extend(_rows_from_page(page, source))
        found = sorted(set(rows))
        present = {label for _, label in found}
        missing = [label for label in _REQUIRED if label not in present]
        response_shape.expect(
            not missing and len(found) >= 20,
            source_name=response_shape.source_name(source),
            detail=(f"PDF yielded {len(found)} collections, missing rounds {missing}"),
            raw=getattr(response, "text", "")[:200],
        )
        return found
