"""Pipeline components for the PDF schedules EKO Sp. z o.o. publishes for Rybnik.

Two layouts, one parser and one reader:

* a district PDF (residential or commercial): page 1 lists the zones (Rejon)
  with their streets, the schedule page prints one block per zone (a row per
  round, a column per month, the days of that month in each cell, ``-`` for a
  season without collection) in the cover's order, and a footer pairs each zone
  with its two bulky-waste dates. The footer's extraction order is unreliable,
  so zone names and dates are grouped into runs and paired by position.
* the city-wide multifamily PDF: a table drawn with ruling lines whose cells
  hold weekday rules ("środa tydzień nieparzysty") rather than dates. The rules
  are expanded over the year with the core recurrence helpers.

:class:`RybnikPdfParser` returns both readings of the file (``pypdf`` text for
the district layout, the ruled grids of :mod:`...service.PdfRuledTable` for the
table) and :class:`RybnikScheduleReader` picks the one the configured property
type needs, yielding ``(date, label)`` rows for an ``ICSTransformer``. The
district registry (slug, zones, footer aliases) is passed in by the source: it
is needed while fetching, so it cannot live in a build-time YAML.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule import (
    date_parsers,
    lookups,
    parsers,
    preprocessors,
    recurrence,
    response_shape,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.service.PdfRuledTable import (
    RuledTableParser,
    merge_split_rows,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Response

# The winter-only ash round is printed with dashes and not surfaced.
_NOT_SURFACED = frozenset({"POPIOŁY/ŻUŻEL"})

_MULTIFAMILY_TYPES = (
    "ZMIESZANE",
    "PLASTIK",
    "PAPIER",
    "SZKŁO",
    "WIELKOGABARYTY",
    "BIO",
)

_WEEKDAYS_PL = {
    "poniedzialek": 0,
    "wtorek": 1,
    "sroda": 2,
    "czwartek": 3,
    "piatek": 4,
    "sobota": 5,
    "niedziela": 6,
}

_ROW_RE = re.compile(
    r"(ZMIESZANE|SEGREGOWANE|BIODEGRADOWALNE|POPIOŁY/ŻUŻEL)"
    r"((?:\s+(?:[\d;]+|-)){12})"
)
_DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})")
_YEAR_RE = re.compile(r"\b(?:na rok|w roku)\s+(20\d\d)")
_parse_dmy = date_parsers.for_format("%d.%m.%Y")


# --- residential / commercial text ----------------------------------------


def _zone_regex(name: str) -> re.Pattern:
    """A regex for a zone name allowing wrapped lines and dropped hyphen gaps."""
    escaped = re.escape(name).replace(r"\-", r"-\s*")
    escaped = re.sub(r"\\\ +", lambda _m: r"\s+", escaped)
    return re.compile(r"(?<![A-Za-z])" + escaped + r"(?!\d)", re.IGNORECASE)


def _rejon_order(text: str, zones: list[str]) -> list[str]:
    """The zones in the order the cover table prints them."""
    start = text.find("Rejony")
    haystack = text[start:] if start >= 0 else text
    found = []
    for zone in zones:
        match = _zone_regex(zone).search(haystack)
        if match:
            found.append((match.start(), zone))
    return [zone for _, zone in sorted(found)]


def _blocks(text: str) -> list[list[tuple[str, list[str]]]]:
    """Groups of round rows, one group per zone (each starts at ZMIESZANE)."""
    rows = [
        (m.group(1), m.group(2).split())
        for m in _ROW_RE.finditer(text)
        if len(m.group(2).split()) == 12
    ]
    starts = [i for i, (key, _) in enumerate(rows) if key == "ZMIESZANE"]
    return [
        rows[start : starts[i + 1] if i + 1 < len(starts) else len(rows)]
        for i, start in enumerate(starts)
    ]


def _bulky_dates(
    text: str, zones: list[str], aliases: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Pair the footer's zone names with their two bulky-waste dates.

    The footer's extraction order is unreliable, so consecutive zones and
    consecutive dates are grouped into runs and each zones-run takes the dates
    of the run before it (then after it), two per zone.
    """
    last = text.rfind("BIODEGRADOWALNE")
    if last < 0:
        return {}
    eol = text.find("\n", last)
    flat = re.sub(r"\s+", " ", text[eol if eol >= 0 else last :]).strip()
    tokens: list[tuple[str, str, int]] = [
        ("date", m.group(1), m.start()) for m in _DATE_RE.finditer(flat)
    ]
    names = {zone: zone for zone in zones}
    for zone in zones:
        for alias in aliases.get(zone, []):
            names[alias] = zone
    seen: set[str] = set()
    for alias in sorted(names, key=len, reverse=True):
        zone = names[alias]
        match = _zone_regex(alias).search(flat)
        if zone not in seen and match:
            tokens.append(("zone", zone, match.start()))
            seen.add(zone)
    tokens.sort(key=lambda t: t[2])
    if not tokens:
        return {}

    runs: list[list[tuple[str, str, int]]] = [[tokens[0]]]
    for token in tokens[1:]:
        if token[0] == runs[-1][-1][0]:
            runs[-1].append(token)
        else:
            runs.append([token])
    pool = {i: [t[1] for t in r] for i, r in enumerate(runs) if r[0][0] == "date"}

    result: dict[str, list[str]] = {}
    for index, run in enumerate(runs):
        if run[0][0] != "zone":
            continue
        remaining = run
        for neighbour in (index - 1, index + 1):
            dates = pool.get(neighbour, [])
            pairs = min(len(dates) // 2, len(remaining))
            for k in range(pairs):
                result[remaining[k][1]] = [dates[2 * k], dates[2 * k + 1]]
            if neighbour in pool:
                pool[neighbour] = dates[pairs * 2 :]
            remaining = remaining[pairs:]
    return result


def _year_of(text: str) -> int:
    match = _YEAR_RE.search(text)
    response_shape.expect(
        match is not None,
        source_name="rybnik_pl",
        detail="no year in the PDF title",
        raw=text[:300],
    )
    assert match is not None
    return int(match.group(1))


def zone_rows(
    text: str, zones: list[str], aliases: dict[str, list[str]], sub_district: str
) -> list[tuple[date, str]]:
    """``(date, label)`` rows of the zones of a district PDF (all, or one)."""
    year = _year_of(text)
    order = _rejon_order(text, zones) or list(zones)
    bulky = _bulky_dates(text, zones, aliases)
    wanted = lookups.normalize_loose(sub_district) if sub_district else ""
    rows: list[tuple[date, str]] = []
    matched = False
    for index, block in enumerate(_blocks(text)):
        zone = order[index] if index < len(order) else f"Zone {index + 1}"
        if wanted:
            if lookups.normalize_loose(zone) != wanted:
                continue
            matched = True
        for key, months in block:
            if key in _NOT_SURFACED:
                continue
            for month, cell in enumerate(months, start=1):
                for day in cell.split(";"):
                    if day.strip().isdigit():
                        try:
                            rows.append((date(year, month, int(day)), key))
                        except ValueError:
                            continue
        rows.extend((_parse_dmy(d), "GABARYTY") for d in bulky.get(zone, []))
    if wanted and not matched:
        raise SourceArgumentNotFoundWithSuggestions("sub_district", sub_district, order)
    return rows


# --- multifamily rules ------------------------------------------------------


def _rows_of(
    grid: list[list[str]], types: tuple[str, ...]
) -> list[tuple[str, list[str], dict[str, str]]]:
    """``(area, streets, {round: rule})`` rows of one multifamily table."""
    header = None
    columns: dict[int, str] = {}
    for r, cols in enumerate(grid):
        found = {
            c: key
            for c, cell in enumerate(cols)
            for key in types
            if lookups.normalize_loose(cell) == lookups.normalize_loose(key)
        }
        if "ZMIESZANE" in found.values():
            header, columns = r, found
            break
    if header is None:
        return []
    area_col, street_col = 0, 1
    for r in range(header + 1):
        for c, cell in enumerate(grid[r]):
            if lookups.normalize_loose(cell) == "dzielnica":
                area_col = c
            elif lookups.normalize_loose(cell) == "ulice":
                street_col = c
    out = []
    for cols in merge_split_rows(grid[header + 1 :], (area_col, street_col)):
        if not cols[area_col]:
            continue
        streets = [s.strip() for s in cols[street_col].split(",") if s.strip()]
        out.append(
            (
                cols[area_col],
                streets,
                {k: cols[c] for c, k in columns.items() if cols[c]},
            )
        )
    return out


_STREET_PREFIX_RE = re.compile(r"^(?:ul|gen|ks|pl|plac|św|sw|kap|os)\.?\s+", re.I)


def _street_keys(name: str) -> set[str]:
    return {
        lookups.normalize_loose(name),
        lookups.normalize_loose(_STREET_PREFIX_RE.sub("", name)),
    }


def select_row(
    rows: list[tuple[str, list[str], dict[str, str]]], street_name: str, area: str
) -> tuple[str, list[str], dict[str, str]]:
    """The row for a street (and area where the street is listed for several)."""
    candidates = rows
    if area:
        candidates = [
            r
            for r in candidates
            if lookups.normalize_loose(r[0]) == lookups.normalize_loose(area)
        ]
        if not candidates:
            raise SourceArgumentNotFoundWithSuggestions(
                "sub_district", area, sorted({r[0] for r in rows})
            )
    if street_name:
        key = lookups.normalize_loose(
            re.sub(r"^\s*ul\.?\s+", "", street_name, flags=re.I)
        )
        matched = [r for r in candidates if any(key in _street_keys(s) for s in r[1])]
        if not matched:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street_name, sorted({s for r in candidates for s in r[1]})
            )
        candidates = matched
    if len({tuple(sorted(r[2].items())) for r in candidates}) > 1:
        if street_name and not area:
            raise SourceArgAmbiguousWithSuggestions(
                "sub_district", area, sorted({r[0] for r in candidates})
            )
        raise SourceArgAmbiguousWithSuggestions(
            "street", street_name, sorted({s for r in candidates for s in r[1]})
        )
    return candidates[0]


def parse_rule(text: str) -> tuple[set[int], str | None]:
    """Weekdays and ISO-week parity ("even"/"odd"/None) of 'środa tydzień parzysty'."""
    weekdays: set[int] = set()
    parity: str | None = None
    for token in re.split(r"[\s,;]+", text):
        word = lookups.normalize_loose(token)
        if not word or word in ("tydzien", "i"):
            continue
        if word in _WEEKDAYS_PL:
            weekdays.add(_WEEKDAYS_PL[word])
        elif word == "parzysty":
            parity = "even"
        elif word == "nieparzysty":
            parity = "odd"
        else:
            raise ValueError(f"Unknown token {token!r} in rule {text!r}")
    if not weekdays:
        raise ValueError(f"No weekday found in rule {text!r}")
    return weekdays, parity


def _first_weekday(year: int, weekday: int) -> date:
    jan1 = date(year, 1, 1)
    return jan1 + timedelta(days=(weekday - jan1.weekday()) % 7)


def _schedules(record: tuple[int, dict[str, str]], _source: Any = None):
    year, rules = record
    for key, rule in rules.items():
        try:
            weekdays, parity = parse_rule(rule)
        except ValueError:
            continue
        for weekday in sorted(weekdays):
            yield preprocessors.Schedule(
                key,
                _first_weekday(year, weekday),
                recurrence.WEEKLY,
                until=date(year, 12, 31),
                not_before=date(year, 1, 1),
                iso_week_parity=parity,  # type: ignore[arg-type]
            )


class RybnikDocument(NamedTuple):
    """Both readings of one schedule PDF."""

    text: str
    grids: list[list[list[str]]]
    table_text: str


class RybnikPdfParser(Parser[RybnikDocument]):
    """Read a Rybnik schedule PDF as ``pypdf`` text plus its ruled table grids."""

    def __init__(self, *, min_chars: int = 200):
        self._text = parsers.PdfTextParser(min_chars=min_chars)
        self._table = RuledTableParser()

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> RybnikDocument:
        tables = self._table(response, source)
        return RybnikDocument(
            text=self._text(response, source),
            grids=tables.grids,
            table_text=tables.text,
        )


class RybnikScheduleReader:
    """Turn a :class:`RybnikDocument` into ``(date, label)`` rows.

    Args:
        districts: ``{district: {"zones": [...], "zone_aliases": {...}}}``.
        multifamily_types: the column headings of the multifamily table.
    """

    def __init__(
        self,
        districts: Mapping[str, Mapping[str, Any]],
        multifamily_types: Iterable[str] = _MULTIFAMILY_TYPES,
    ):
        self.districts = districts
        self.multifamily_types = tuple(multifamily_types)

    def __call__(
        self, document: RybnikDocument, source: BaseSource
    ) -> list[tuple[date, str]]:
        params = source.params
        if params["property_type"] == "multifamily":
            return self._multifamily(document, params)
        cfg = lookups.resolve(self.districts, params["district"], argument="district")
        return zone_rows(
            document.text,
            cfg["zones"],
            cfg.get("zone_aliases", {}),
            (params["sub_district"] or "").strip(),
        )

    def _multifamily(
        self, document: RybnikDocument, params: Mapping[str, Any]
    ) -> list[tuple[date, str]]:
        street_name = (params["street"] or "").strip()
        area = (params["sub_district"] or "").strip()
        if not street_name and not area:
            raise SourceArgumentRequired(
                "street", "street is required for property_type 'multifamily'"
            )
        rows = [
            row
            for grid in document.grids
            for row in _rows_of(grid, self.multifamily_types)
        ]
        response_shape.expect(
            bool(rows),
            source_name="rybnik_pl",
            detail="no rows in the multifamily table",
            raw=document.table_text[:300],
        )
        _, _, rules = select_row(rows, street_name, area)
        year = _year_of(document.table_text)
        return list(preprocessors.RecurrenceExpander(_schedules)([(year, rules)]))
