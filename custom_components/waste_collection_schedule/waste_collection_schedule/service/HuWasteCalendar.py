"""Pipeline components for Hungarian annual waste calendars.

Depónia (deponia.hu), Siókom (siokom.hu) and Dunanett (dunanett.hu)
publish the same annual calendar, exported from a
PowerPoint template: one table with a column per month and a row per separately
collected waste type (``szelektív``, ``zöldhulladék``, ...) listing the days of
the month ("3.,17.,31." or "1,8,15,22, 29"), and a sentence below it that
names the weekday(s) of the weekly general-waste round ("Vegyes
hulladékgyűjtési nap: KEDD,PÉNTEK"), optionally restricted to date ranges
("01.01-03.31 és 11.01-12.31 között CSÜTÖRTÖK") or moved by a public holiday
("2026.05.01. áthelyezésre kerül 2026.05.02").

:class:`CalendarParser` decodes the PDF into ``(date, label)`` records. The
labels are the Hungarian words printed in the PDF (plus :data:`GENERAL` and
:data:`BULKY` for the two rounds that are not table rows), which the source's
``ICSTransformer`` maps onto waste types. The month of a day cell is the month
header nearest to it in the layout text. A PDF without a year, without the
month header or without any date fails loudly instead of returning nothing.

``MonthTableCalendarParser`` reads the corresponding HTML/DOCX month-and-day
tables. ``PublishedCalendarsParser`` checks downloaded calendars against their
publication index, including files without a year in their download URL.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, timedelta
from io import BytesIO
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from waste_collection_schedule import parsers, response_shape
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

#: Labels for the two rounds that are not rows of the month table.
GENERAL = "vegyes"
BULKY = "lomtalanítás"
CHRISTMAS_TREES = "fenyőfa"
CHRISTMAS_TREE_DESCRIPTION = (
    "Christmas trees only: remove all decorations and other waste. "
    "Other garden waste is not collected on this date."
)

MONTHS = {
    "január": 1,
    "február": 2,
    "március": 3,
    "április": 4,
    "május": 5,
    "június": 6,
    "július": 7,
    "augusztus": 8,
    "szeptember": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}

WEEKDAYS = {
    "hétfő": 0,
    "kedd": 1,
    "szerda": 2,
    "csütörtök": 3,
    "péntek": 4,
    "szombat": 5,
    "vasárnap": 6,
}

_YEAR_RE = re.compile(r"(20\d{2})\.\s*évi\s+hulladéknaptár", re.IGNORECASE)
_JANUARY_TREES_RE = re.compile(
    r"a januari zoldhulladekgyujtes soran kizarolag[^.]*fenyofakat szallitjuk el",
)
#: Day-list notations of a month cell: "14,28" / "1,8,15,22, 29" (Siókom).
PLAIN_CELLS = r"-|\d{1,2}(?:[.,]\s*\d{1,2}){1,6}\.?|\d{1,2}\.?"
#: and "3.,17.,31." / "14. 28" (Depónia).
DOTTED_CELLS = (
    r"-|\d{1,2}(?:\.,\d{1,2}){1,3}\.?|\d{1,2}[.,]\s{1,2}\d{1,2}"
    r"|\d{1,2}\.\d{1,2}\.?|\d{1,2}\.?"
)
_DAY_RE = re.compile(r"\d{1,2}")

_RANGE_NC = r"\d{1,2}\.\d{1,2}\s*-\s*\d{1,2}\.\d{1,2}"
_WD_NC = "|".join(WEEKDAYS)
_RANGED_RULE_RE = re.compile(
    rf"((?:{_RANGE_NC}(?:\s+és\s+{_RANGE_NC})*)\s+között)\s+"
    rf"(({_WD_NC})(?:\s+és\s+(?:{_WD_NC}))*)",
    re.IGNORECASE,
)
_RANGE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\s*-\s*(\d{1,2})\.(\d{1,2})")
_COMMUNAL_RE = re.compile(
    r"Vegyes\s+hulladékgyűjtési\s+nap\s*:(.*)", re.IGNORECASE | re.DOTALL
)
_COMMUNAL_END_RE = re.compile(
    r"Szolgáltató|Lomtalanítás|Kérjük|Hulladékudvar|20\d{2}", re.IGNORECASE
)
_ISO_POSTPONE_RE = re.compile(
    r"(20\d{2})\.(\d{2})\.(\d{2})\.[^.]*?áthelyezésre kerül\s*"
    r"(20\d{2})\.(\d{2})\.(\d{2})",
    re.IGNORECASE,
)
_HU_POSTPONE_RE = re.compile(
    r"áthelyezés:\s*(\w+)\s+(\d{1,2})\.\s*gyűjtés\s*(\w+)\s+(\d{1,2})",
    re.IGNORECASE,
)
_BULKY_ISO_RE = re.compile(
    r"Lomtalanítás\s*:?\s*(20\d{2})\.(\d{1,2})\.(\d{1,2})", re.IGNORECASE
)
_BULKY_HU_RE = re.compile(
    r"(20\d{2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{1,2})", re.IGNORECASE
)


def fold(value: str) -> str:
    """Case- and accent-insensitive form of ``value`` for comparing names."""
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    collapsed = re.sub(r"\s+", " ", stripped).strip().casefold()
    return re.sub(r"\s*-\s*", "-", collapsed)


def month_columns(line: str) -> list[tuple[int, int]] | None:
    """``(position, month)`` of the twelve month names in a header line."""
    low = line.lower()
    if "január" not in low or "december" not in low:
        return None
    cols = sorted(
        (low.find(name), number) for name, number in MONTHS.items() if name in low
    )
    return cols if len(cols) == 12 else None


def table_row_dates(
    line: str,
    year: int,
    columns: list[tuple[int, int]],
    types: Mapping[str, str],
    *,
    skip: re.Pattern[str],
    cells: re.Pattern[str] = re.compile(PLAIN_CELLS),
    max_length: int | None = None,
    strict: bool = False,
    source_name: str = "source",
) -> list[tuple[date, str]]:
    """The dated cells of one table row, labelled with the row's waste type.

    ``types`` maps the (lowercase) row label printed in the PDF to the label to
    emit. Lines of running text that merely mention a type are ignored: they
    match ``skip``, exceed ``max_length`` or carry no day after the label.
    """
    if skip.search(line) or (max_length is not None and len(line) > max_length):
        return []
    pattern = r"\b(" + "|".join(re.escape(label) for label in types) + r")\b"
    match = re.search(pattern, line, re.IGNORECASE)
    if not match:
        return []
    label_end = match.end()
    after = line[label_end:]
    if strict:
        matches = list(cells.finditer(after))
        months = [
            min(columns, key=lambda col: abs(col[0] - label_end - cell.start()))[1]
            for cell in matches
        ]
        response_shape.expect(
            len(matches) == 12
            and sorted(months) == list(range(1, 13))
            and not cells.sub("", after).strip(),
            source_name=source_name,
            detail="expected twelve complete month cells for each waste row",
            raw=line,
        )
    if not re.search(r"\d|-", after):
        return []
    label = types[match.group(1).lower()]
    entries: list[tuple[date, str]] = []
    for cell in cells.finditer(after):
        token = cell.group()
        if token in ("-", "–", "—") or not _DAY_RE.search(token):
            continue
        position = label_end + cell.start()
        month = min(columns, key=lambda col: abs(col[0] - position))[1]
        for day in (int(item) for item in _DAY_RE.findall(token)):
            try:
                entries.append((date(year, month, day), label))
            except ValueError:
                if strict:
                    response_shape.expect(
                        False,
                        source_name=source_name,
                        detail=f"invalid calendar date {year}-{month}-{day}",
                        raw=line,
                    )
                _LOGGER.debug("Ignoring invalid date %s-%s-%s", year, month, day)
    return entries


def weekdays_in(text: str) -> list[int]:
    """The weekdays (Monday is 0) named in ``text``, in any case or accent."""
    folded = fold(text)
    return sorted(
        {wd for name, wd in WEEKDAYS.items() if re.search(rf"\b{fold(name)}\b", folded)}
    )


def dates_in_range(start: date, end: date, weekdays: Iterable[int]) -> list[date]:
    """Every date from ``start`` to ``end`` (inclusive) on one of ``weekdays``."""
    wanted = set(weekdays)
    return [
        start + timedelta(days=offset)
        for offset in range((end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() in wanted
    ]


def general_waste_dates(text: str, year: int) -> list[date]:
    """The weekly general-waste days from the "Vegyes hulladékgyűjtési nap" text.

    Either plain weekdays for the whole year ("KEDD,PÉNTEK") or one rule per
    date range ("01.01-03.31 és 11.01-12.31 között CSÜTÖRTÖK").
    """
    match = _COMMUNAL_RE.search(text)
    if not match:
        return []
    rest = _COMMUNAL_END_RE.split(match.group(1), maxsplit=1)[0]
    if _RANGE_RE.search(match.group(1)):
        # the range rules contain no year, so cut only at the footer words
        rest = re.split(
            r"Szolgáltató|Lomtalanítás|Kérjük|Hulladékudvar",
            match.group(1),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
    rest = re.sub(r"\s+", " ", rest).strip()
    dated: set[date] = set()
    if _RANGE_RE.search(rest):
        for rule in _RANGED_RULE_RE.finditer(rest):
            weekdays = weekdays_in(rule.group(2))
            for start_m, start_d, end_m, end_d in _RANGE_RE.findall(rule.group(1)):
                try:
                    start = date(year, int(start_m), int(start_d))
                    end = date(year, int(end_m), int(end_d))
                except ValueError:
                    continue
                dated.update(dates_in_range(start, end, weekdays))
    else:
        weekdays = weekdays_in(rest)
        if weekdays:
            dated.update(dates_in_range(date(year, 1, 1), date(year, 12, 31), weekdays))
    return sorted(dated)


def postponements(text: str, year: int) -> list[tuple[date, date]]:
    """``(from, to)`` pairs of the holiday moves announced in the PDF."""
    moves: list[tuple[date, date]] = []
    for match in _ISO_POSTPONE_RE.finditer(text):
        try:
            moves.append(
                (
                    date(int(match.group(1)), int(match.group(2)), int(match.group(3))),
                    date(int(match.group(4)), int(match.group(5)), int(match.group(6))),
                )
            )
        except ValueError:
            continue
    for match in _HU_POSTPONE_RE.finditer(text):
        src_month = MONTHS.get(match.group(1).lower())
        dst_month = MONTHS.get(match.group(3).lower())
        if not src_month or not dst_month:
            continue
        try:
            moves.append(
                (
                    date(year, src_month, int(match.group(2))),
                    date(year, dst_month, int(match.group(4))),
                )
            )
        except ValueError:
            continue
    return moves


def apply_postponements(
    dates: Iterable[date], moves: Iterable[tuple[date, date]]
) -> list[date]:
    """``dates`` with every date named as the start of a move shifted."""
    remaining = set(dates)
    for src, dst in moves:
        if src in remaining:
            remaining.remove(src)
            remaining.add(dst)
    return sorted(remaining)


def bulky_dates(text: str) -> list[date]:
    """Dated bulky-waste collections ("Lomtalanítás: 2026.05.16.")."""
    dates: set[date] = set()
    for match in _BULKY_ISO_RE.finditer(text):
        try:
            dates.add(
                date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            )
        except ValueError:
            continue
    if re.search(r"Lomtalanítási\s+időpontok", text, re.IGNORECASE):
        for match in _BULKY_HU_RE.finditer(text):
            try:
                dates.add(
                    date(
                        int(match.group(1)),
                        MONTHS[match.group(2).lower()],
                        int(match.group(3)),
                    )
                )
            except ValueError:
                continue
    return sorted(dates)


class CalendarParser(Parser["list[tuple[date, str]]"]):
    """Decode a Hungarian hulladéknaptár PDF into ``(date, label)``.

    Args:
        types: the table row labels to read (lowercase, as printed) and the
            label emitted for each.
        skip: a pattern marking running-text lines that mention a type.
        cells: the day-list notation of a month cell, :data:`PLAIN_CELLS` or
            :data:`DOTTED_CELLS`.
        max_row_length: ignore lines longer than this (running text).
        bulky: also read dated bulky-waste collections, emitted as
            :data:`BULKY`.
        holiday_moves: apply the announced holiday moves of the weekly
            general-waste round.
        strict: require every configured row, twelve complete month cells per
            row, valid dates and a weekly general-waste rule.
        expected_municipality: exact municipality in the annual heading; a
            literal or a callable receiving the source parameters.
        year_from_url: require the PDF filename's year to match its heading;
            a boolean or a callable receiving the source parameters.
        january_trees: relabel January garden dates as :data:`CHRISTMAS_TREES`
            only when the PDF explicitly restricts them to undecorated trees.
            Map that label to garden waste and carry its restriction metadata.
    """

    def __init__(
        self,
        *,
        types: Mapping[str, str],
        skip: str = r"gyűjtés:|gyűjtésbe|gyűjtést|anyagok",
        cells: str = PLAIN_CELLS,
        max_row_length: int | None = None,
        bulky: bool = False,
        holiday_moves: bool = False,
        strict: bool = False,
        expected_municipality: str | Callable[..., str] | None = None,
        year_from_url: bool | Callable[..., bool] = False,
        january_trees: bool = False,
    ) -> None:
        self.types = {key.lower(): value for key, value in types.items()}
        self.skip = re.compile(skip, re.IGNORECASE)
        self.cells = re.compile(cells)
        self.max_row_length = max_row_length
        self.bulky = bulky
        self.holiday_moves = holiday_moves
        self.strict = strict
        self.expected_municipality = expected_municipality
        self.year_from_url = year_from_url
        self.january_trees = january_trees

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        from pypdf import PdfReader

        name = response_shape.source_name(source)
        reader = PdfReader(BytesIO(response.content))
        layouts = [
            page.extract_text(extraction_mode="layout") or "" for page in reader.pages
        ]
        plains = [page.extract_text() or "" for page in reader.pages]
        combined = "\n".join([*layouts, *plains])

        year_match = _YEAR_RE.search(combined)
        response_shape.expect(
            year_match is not None,
            source_name=name,
            detail="no 'YYYY. évi hulladéknaptár' heading in the PDF",
            raw=combined[:500],
        )
        year = int(year_match.group(1))  # type: ignore[union-attr]
        year_from_url = (
            self.year_from_url(**(source.params if source else {}))
            if callable(self.year_from_url)
            else self.year_from_url
        )
        if year_from_url:
            years = re.findall(
                r"20\d{2}", unquote(urlsplit(response.url).path).rsplit("/", 1)[-1]
            )
            response_shape.expect(
                years == [str(year)],
                source_name=name,
                detail="PDF filename year does not match the annual heading",
                raw=response.url,
            )
        if self.expected_municipality is not None:
            wanted = (
                self.expected_municipality(**(source.params if source else {}))
                if callable(self.expected_municipality)
                else self.expected_municipality
            )
            heading = re.search(
                _YEAR_RE.pattern + r"\s*[-–—]\s*([^\n]+)",
                "\n".join(layouts),
                re.IGNORECASE,
            )
            response_shape.expect(
                heading is not None and fold(heading.group(2)) == fold(wanted),
                source_name=name,
                detail="annual heading does not match the expected municipality",
                raw=combined[:500],
            )

        columns = None
        table_page = 0
        for index, layout in enumerate(layouts):
            for line in layout.splitlines():
                columns = month_columns(line)
                if columns:
                    break
            if columns:
                table_page = index
                break
        response_shape.expect(
            columns is not None,
            source_name=name,
            detail="no month table in the PDF",
            raw=combined[:500],
        )

        dated: list[tuple[date, str]] = []
        seen_types: set[str] = set()
        in_table = not self.strict
        for line in layouts[table_page].splitlines():
            if self.strict:
                if month_columns(line):
                    in_table = True
                    continue
                if _COMMUNAL_RE.search(line):
                    break
                if not in_table:
                    continue
            dated.extend(
                table_row_dates(
                    line,
                    year,
                    columns,  # type: ignore[arg-type]
                    self.types,
                    skip=self.skip,
                    cells=self.cells,
                    max_length=self.max_row_length,
                    strict=self.strict,
                    source_name=name,
                )
            )
            if self.strict and not self.skip.search(line):
                seen_types.update(
                    label
                    for label in self.types
                    if re.search(rf"\b{re.escape(label)}\b", line, re.IGNORECASE)
                )

        weekly = general_waste_dates(plains[table_page], year) or general_waste_dates(
            layouts[table_page], year
        )
        if self.strict:
            response_shape.expect(
                bool(weekly) and set(self.types) <= seen_types,
                source_name=name,
                detail="missing required waste row or general-waste rule",
                raw=layouts[table_page],
            )
        if self.january_trees and _JANUARY_TREES_RE.search(fold(combined)):
            garden = self.types.get("zöldhulladék")
            dated = [
                (
                    when,
                    CHRISTMAS_TREES if when.month == 1 and label == garden else label,
                )
                for when, label in dated
            ]
        if weekly and self.holiday_moves:
            weekly = apply_postponements(weekly, postponements(combined, year))
        dated.extend((when, GENERAL) for when in weekly)
        if self.bulky:
            dated.extend((when, BULKY) for when in bulky_dates(combined))

        response_shape.expect(
            bool(dated),
            source_name=name,
            detail="no collection dates found in the PDF",
            raw=combined[:500],
        )
        return sorted(set(dated)) if self.strict else sorted(dated)


class PublishedCalendarsParser(Parser["list[tuple[date, str]]"]):
    """Validate downloaded calendars against the years in their publication index.

    Pair with ``FanOutRetriever(include_prepared=True)`` whose prepare returns
    the index response. ``discover(response, **params)`` is the same pure pick
    used by its targets, returning ordered ``(url, year)`` pairs. Keeping the
    real index alongside the downloads also handles yearless/UUID filenames.
    """

    def __init__(
        self, *, discover: Callable[..., list[tuple[str, int]]], parser: Parser
    ) -> None:
        self.discover = discover
        self.parser = parsers.EachResponse(parser)

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        index, *documents = response
        targets = self.discover(index, **(source.params if source else {}))
        name = response_shape.source_name(source)
        response_shape.expect(
            len(documents) == len(targets),
            source_name=name,
            detail="publication index and downloaded calendar count disagree",
            raw=targets,
        )
        records: list[tuple[date, str]] = []
        for document, (url, year) in zip(documents, targets, strict=True):
            dated = self.parser([document], source)
            response_shape.expect(
                bool(dated) and {when.year for when, _ in dated} == {year},
                source_name=name,
                detail="calendar heading year disagrees with its publication index",
                raw=(url, year),
            )
            records.extend(dated)
        return records


_ROMAN_MONTHS = (
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
)
_MONTH_NUMBERS = {fold(name): number for name, number in MONTHS.items()}
_MONTH_NUMBERS.update(
    {name.lower(): number for number, name in enumerate(_ROMAN_MONTHS, 1)}
)


def _month_table_dates(
    rows: list[list[str]], year: int, label: str, *, trees: bool, name: str
) -> list[tuple[date, str]]:
    """Read alternating month/day rows, preserving explicitly omitted months."""
    response_shape.expect(
        len(rows) in (2, 4),
        source_name=name,
        detail="expected paired month and day rows",
        raw=rows,
    )
    dated: list[tuple[date, str]] = []
    seen: list[int] = []
    for headers, cells in zip(rows[::2], rows[1::2], strict=True):
        months = [_MONTH_NUMBERS.get(fold(cell).rstrip(".")) for cell in headers]
        response_shape.expect(
            bool(months) and len(months) == len(cells) and all(months),
            source_name=name,
            detail="invalid month headings or unequal day cells",
            raw=rows,
        )
        for month, cell in zip(months, cells, strict=True):
            assert month is not None
            seen.append(month)
            token = cell.strip()
            response_shape.expect(
                re.fullmatch(r"-|\d{1,2}(?:(?:\.?\s+|\s*[/,]\s*)\d{1,2})*\.?", token)
                is not None,
                source_name=name,
                detail="invalid month day list",
                raw=cell,
            )
            days = [int(day) for day in re.findall(r"\d+", token)]
            response_shape.expect(
                days == sorted(set(days)),
                source_name=name,
                detail="duplicate or unordered days in month cell",
                raw=cell,
            )
            for day in days:
                try:
                    when = date(year, month, day)
                except ValueError:
                    raise response_shape.ResponseShapeError(
                        name, "invalid calendar date"
                    ) from None
                dated.append((when, CHRISTMAS_TREES if trees and month == 1 else label))
    response_shape.expect(
        seen == sorted(set(seen))
        and (label != "szelektív" or seen == list(range(1, 13))),
        source_name=name,
        detail="missing, duplicate or unordered month columns",
        raw=rows,
    )
    return dated


def _docx_blocks(content: bytes, name: str) -> list[str | list[list[str]]]:
    """Extract body paragraphs and table cells from a real DOCX ZIP, in order."""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    def text(element: ElementTree.Element) -> str:
        return (
            " ".join(
                "".join(node.text or "" for node in paragraph.findall(".//w:t", ns))
                for paragraph in element.iterfind(".//w:p", ns)
            )
            if element.tag.endswith("}tc")
            else "".join(node.text or "" for node in element.findall(".//w:t", ns))
        )

    try:
        with ZipFile(BytesIO(content)) as archive:
            # ElementTree does not resolve external entities.
            root = ElementTree.fromstring(archive.read("word/document.xml"))  # nosec B314
    except (BadZipFile, KeyError, ElementTree.ParseError) as error:
        raise response_shape.ResponseShapeError(
            name, "invalid DOCX calendar"
        ) from error
    body = root.find("w:body", ns)
    response_shape.expect(
        body is not None,
        source_name=name,
        detail="missing DOCX body",
        raw=content[:100],
    )
    assert body is not None
    return [
        [
            [text(cell) for cell in row.findall("w:tc", ns)]
            for row in element.findall("w:tr", ns)
        ]
        if element.tag.endswith("}tbl")
        else text(element)
        for element in body
        if element.tag.endswith(("}tbl", "}p"))
    ]


def _article_general_dates(text: str, year: int, name: str) -> list[date]:
    """Require both named areas to share the explicitly stated target weekday.

    The weekday *before* ``helyett`` is the superseded round, never a target.
    An altered or area-dependent rule needs investigation rather than guessing.
    """
    weekday = "|".join(fold(day) for day in WEEKDAYS)
    rule = re.fullmatch(
        rf"melykut telepulesreszen valtozik a kommunalis hulladekszallitas rendje\s*:\s*"
        rf"a korabbi (?:{weekday})i nap helyett (?P<changed>{weekday})i napokon "
        rf"tortenik a hulladekszallitas\. a kozponti telepulesreszen valtozatlanul "
        rf"(?P<central>{weekday})i napon kerul elszallitasra a kommunalis hulladek\.",
        fold(text),
    )
    response_shape.expect(
        rule is not None and rule["changed"] == rule["central"],
        source_name=name,
        detail="unrecognised or area-dependent annual general-waste rule",
        raw=text,
    )
    assert rule is not None
    return dates_in_range(
        date(year, 1, 1), date(year, 12, 31), weekdays_in(rule["changed"])
    )


class MonthTableCalendarParser(Parser["list[tuple[date, str]]"]):
    """Hungarian annual HTML/DOCX calendars with month headings above day lists.

    HTML uses the annual article heading and its two labelled tables; DOCX uses
    the printed heading and body/table order. A garden table may omit months;
    those omissions are not recurrence rules. January tree restrictions are
    detected from the publication, and no absent residual rule is invented.
    """

    def __init__(self, *, docx: bool = False) -> None:
        self.docx = docx

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        name = response_shape.source_name(source)
        wanted = fold(source.params["municipality"]) if source else ""
        weekly: list[date] = []
        if self.docx:
            blocks = _docx_blocks(response.content, name)
            heading = " ".join(block for block in blocks if isinstance(block, str))
            match = re.search(
                r"hulladekgyujtes\s+(20\d{2})\s*\.\s*evben", fold(heading)
            )
        else:
            headings = parsers.HtmlParser("h1")(response)
            contents = parsers.HtmlParser(".entry-content")(response)
            response_shape.expect(
                len(headings) == len(contents) == 1,
                source_name=name,
                detail="expected one annual article and heading",
                raw=response.text[:500],
            )
            heading = headings[0].get_text(" ", strip=True)
            match = re.fullmatch(
                r"tajekoztato a hulladekszallitas (20\d{2})\.? evi rendjerol",
                fold(heading),
            )
            blocks = [
                [
                    [
                        cell.get_text(" ", strip=True)
                        for cell in row.find_all(["td", "th"], recursive=False)
                    ]
                    for row in element.select("tr")
                ]
                if element.name == "table"
                else element.get_text(" ", strip=True)
                for element in contents[0].find_all(["p", "table"], recursive=False)
            ]
            heading += " " + contents[0].get_text(" ", strip=True)
        response_shape.expect(
            match is not None
            and bool(wanted)
            and re.search(rf"\b{re.escape(wanted)}(?:en)?\b", fold(heading))
            is not None,
            source_name=name,
            detail="missing annual heading or wrong municipality",
            raw=heading[:500],
        )
        assert match is not None
        year = int(match[1])
        dated: list[tuple[date, str]] = []
        seen: list[str] = []
        label = ""
        restriction = ""
        for block in blocks:
            if isinstance(block, str):
                text = fold(block)
                if re.fullmatch(
                    r"(?:a )?szelektiv hulladek(?:szallitas idopontjai| gyujtes)\s*:",
                    text,
                ):
                    label, restriction = "szelektív", ""
                elif re.fullmatch(
                    r"(?:biologiailag lebomlo hulladek elszallitasanak idopontjai|zoldhulladek gyujtes)\s*:",
                    text,
                ):
                    label, restriction = "zöldhulladék", ""
                else:
                    restriction += " " + text
                if not self.docx and "kommunalis hulladekszallitas rendje" in text:
                    response_shape.expect(
                        not weekly,
                        source_name=name,
                        detail="duplicate general-waste rule",
                        raw=block,
                    )
                    weekly = _article_general_dates(block, year, name)
                continue
            response_shape.expect(
                bool(label) and label not in seen,
                source_name=name,
                detail="missing or duplicate table label",
                raw=block,
            )
            seen.append(label)
            trees = bool(
                re.search(
                    r"januarban csak karacsonyfat szallitanak el|a januari zoldhulladek\s*gyujtes soran kizarolag[^.]*fenyofakat szallitjak el",
                    restriction,
                )
            )
            dated.extend(_month_table_dates(block, year, label, trees=trees, name=name))
            label = ""
        response_shape.expect(
            seen == ["szelektív", "zöldhulladék"]
            and bool(dated)
            and (self.docx or bool(weekly)),
            source_name=name,
            detail="missing annual collection table or general-waste rule",
            raw=heading[:500],
        )
        dated.extend((when, GENERAL) for when in weekly)
        return sorted(set(dated))
