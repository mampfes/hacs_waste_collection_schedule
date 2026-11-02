"""UAB "Telšių keliai", Telšiai district municipality, Lithuania.

The address calendar on ``tkeliai.lt/kalendorius`` no longer lists any
location (its ``ajax.php`` answers an empty list). The schedule is published
as yearly PDF notices instead, linked from the "Atliekų tvarkymas" page: one
for the town of Telšiai and one for the villages. Each notice ("GYVENTOJŲ
ŽINIAI") names the streets or villages of one route and prints two tables for
the year, month by month: the mixed municipal waste days, and the packaging
days with their round in brackets, "KP" (other packaging), "SP" (glass) or
both ("1;29 (KP);30 (SP)", "5 (KP+SP)"). Every notice is printed twice per
page, for cutting out.

The source reads both PDFs of every year from the current one on, finds the
notice that lists the configured location and reports its dates. Nothing is
derived from the weekday the notice names.
"""

import datetime
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.field_terms import STREET
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://tkeliai.lt/atlieku-tvarkymas"
_TOWN_PDF = retrievers.yearly_links(r"/(20\d\d)[^/]*miest[^/]*\.pdf$")
_VILLAGES_PDF = retrievers.yearly_links(r"/(20\d\d)[^/]*kaim[^/]*\.pdf$")

_MIXED = "Mišrios komunalinės atliekos"
_ROUNDS = {
    "KP": "Kitos pakuočių atliekos",
    "SP": "Stiklo pakuočių atliekos",
}
_TYPES = {
    _MIXED: wt.GENERAL_WASTE,
    _ROUNDS["KP"]: wt.RECYCLABLES,
    _ROUNDS["SP"]: wt.GLASS,
}

# Month names as the notices print them, upper case. pypdf sometimes splits a
# word at a kerning pair ("V ASARIS", "KOV AS"), so a space may follow any
# letter.
_MONTH = r"((?:[A-ZĄČĘĖĮŠŲŪŽ] ?){4,10})"
_ROW = re.compile(
    rf"^\s*{_MONTH}\s+(\d[\d;\s]*?)\s+{_MONTH}\s+(\S.*?)\s*$", re.MULTILINE
)
_PACKAGING = re.compile(r"([\d;\s]+)\(\s*([A-Z+\s]+?)\s*\)")
_YEAR = re.compile(r"(20\d\d)\s+metai")
_DISTRICT = re.compile(r"^\s*(\S+)\s+seni[uū]nij\s*(?:a|os)\s*:\s*", re.IGNORECASE)
# Words of a house-number range that carry no information: "nuo 1 iki 31".
_RANGE_WORDS = {"nuo", "iki", "ir", "nr"}
_MISSING_COMMA = re.compile(
    r"(?:(?<=\d[a-z]\.)|(?<=\d\.)|(?<=\)))\s+(?=[A-ZĄČĘĖĮŠŲŪŽ][a-ząčęėįšųūž]{2,})"
)
# A street or village type a location may end in: "Žalioji g.", "Paragai k.".
_TYPE_SUFFIX = re.compile(r"\s+(?:g|k|g-vė|gatvė|kaimas)\.?\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class _Entry:
    """One street or village of a notice, as printed and as matched."""

    display: str
    name: str
    qualifier: str
    district: str


@dataclass
class _Notice:
    year: int
    entries: list[_Entry]
    rows: list[tuple[datetime.date, str]]


def _compact(text: str) -> str:
    """Loose form without spaces, robust against the PDF's split words."""
    return lookups.normalize_loose(text).replace(" ", "")


def _qualifier(text: str) -> str:
    words = lookups.normalize_loose(text).split()
    joined = " ".join(w for w in words if w not in _RANGE_WORDS)
    # "19 b" and "19b" are the same house number.
    return re.sub(r"(\d) ([a-z])\b", r"\1\2", joined).replace(" ", "")


def _split_location(text: str) -> tuple[str, str]:
    """'Butkų Juzės(1-31) g.' -> ('Butkų Juzės', '1-31')."""
    text = _TYPE_SUFFIX.sub("", text.strip().rstrip(","))
    qualifiers = re.findall(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", text)
    name = re.sub(r"\([^()]*(?:\([^()]*\)[^()]*)*\)", " ", text)
    numbers = re.search(r"\s(\d[\w;,.\s-]*)$", name)
    if numbers:
        qualifiers.append(numbers.group(1))
        name = name[: numbers.start()]
    name = _TYPE_SUFFIX.sub("", name.strip().rstrip("."))
    return name.strip(), " ".join(qualifiers)


def _entries(header: str) -> list[_Entry]:
    district = ""
    match = _DISTRICT.match(header)
    if match:
        district = f"{match.group(1)} seniūnija"
        header = header[match.end() :]
    header = re.sub(r"gatvių\s+individualūs\s+namai\.?", "", header)
    parts, depth, current = [], 0, ""
    for char in header:
        depth += {"(": 1, ")": -1}.get(char, 0)
        if char == "," and depth <= 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    # A few commas are missing in print: "Respublikos 24b. Rožių",
    # "V. Mačernio (3A-61; 22-92) Saulės". A capitalised word right after a
    # house number or a closing bracket starts the next street.
    parts = [piece for part in parts for piece in _MISSING_COMMA.split(part)]
    entries = []
    for part in parts:
        # Garden communities: "Sodai : Aitvaras", "Žilvičiai_Sodai : Ąžuolas".
        part = " ".join(part.split(":")[-1].split()).strip(" .")
        if not part:
            continue
        name, qualifier = _split_location(part)
        if not _compact(name):
            continue
        display = f"{part}, {district}" if district else part
        entries.append(_Entry(display, _compact(name), _qualifier(qualifier), district))
    return entries


def _month(word: str) -> int:
    number = recurrence.month(word.replace(" ", "").capitalize(), "lt")
    if number is None:
        raise ValueError(f"not a Lithuanian month: {word!r}")
    return number


def _days(text: str) -> list[int]:
    return [int(day) for day in re.findall(r"\d+", text)]


def _notices(text: str, source: "BaseSource | None" = None) -> Iterator[_Notice]:
    """Every distinct notice of one PDF, with its dated rows."""
    seen: set[str] = set()
    for block in re.split(r"GYVENTOJŲ\s+ŽINIAI", str(text))[1:]:
        year_match = _YEAR.search(block)
        if year_match is None:
            continue
        header = " ".join(block[: year_match.start()].split())
        if _compact(header) in seen:
            continue
        seen.add(_compact(header))
        year = int(year_match.group(1))
        rows: list[tuple[datetime.date, str]] = []
        months = list(_ROW.finditer(block[year_match.end() :]))
        if len(months) != 12:
            raise ValueError(
                f"tkeliai_lt: expected 12 month rows for {header[:60]!r}, "
                f"found {len(months)}; the notice layout may have changed"
            )
        for row in months:
            mixed_month, mixed, packaging_month, packaging = row.groups()
            for day in _days(mixed):
                rows.append((datetime.date(year, _month(mixed_month), day), _MIXED))
            month = _month(packaging_month)
            for days, codes in _PACKAGING.findall(packaging):
                for day in _days(days):
                    for code in re.split(r"\s*\+\s*", codes.strip()):
                        rows.append((datetime.date(year, month, day), _ROUNDS[code]))
        if rows:
            yield _Notice(year, _entries(header), rows)


def _matching(notices: list[_Notice], location: str) -> list[_Notice]:
    """The notices of one year that list the location."""
    text, district = location, ""
    if "," in location:
        head, tail = location.rsplit(",", 1)
        if "seni" in tail.casefold():
            text, district = head, _compact(tail)
    name, qualifier = _split_location(text)
    name, qualifier = _compact(name), _qualifier(qualifier)
    candidates = [
        (notice, entry)
        for notice in notices
        for entry in notice.entries
        if entry.name == name and (not district or _compact(entry.district) == district)
    ]
    if qualifier:
        candidates = [c for c in candidates if c[1].qualifier == qualifier]
    elif any(not entry.qualifier for _, entry in candidates):
        candidates = [c for c in candidates if not c[1].qualifier]
    found: list[_Notice] = []
    for notice, _ in candidates:
        if all(notice.rows != other.rows for other in found):
            found.append(notice)
    if len(found) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "location", location, sorted({entry.display for _, entry in candidates})
        )
    return found


def _rows(
    notices: Iterable[_Notice], source: "BaseSource | None"
) -> Iterator[tuple[datetime.date, str]]:
    location = str(source.params["location"]) if source is not None else ""
    by_year: dict[int, list[_Notice]] = {}
    for notice in notices:
        by_year.setdefault(notice.year, []).append(notice)
    matched = False
    for year in sorted(by_year):
        for notice in _matching(by_year[year], location):
            matched = True
            yield from notice.rows
    if not matched and by_year:
        latest = by_year[max(by_year)]
        raise SourceArgumentNotFoundWithSuggestions(
            "location",
            location,
            sorted({entry.display for notice in latest for entry in notice.entries}),
        )


def _both_pdfs(response: Any, *keys: Any, **params: Any) -> list[str]:
    return _TOWN_PDF(response, *keys, **params) + _VILLAGES_PDF(
        response, *keys, **params
    )


@final
class Source(BaseSource):
    TITLE = "Telšių keliai"
    DESCRIPTION = "Source script for UAB 'Telšių keliai'"
    URL = "https://tkeliai.lt/"
    COUNTRY = "lt"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GLASS]

    TEST_CASES: ClassVar[dict] = {
        "TestName1": {"location": "Butkų Juzės(1-31) g."},
        "TestName2": {"location": "Paragai k."},
        "TestName3": {"location": "Žalioji g."},
        "Gintalai, Varnių seniūnija": {"location": "Gintalai, Varnių seniūnija"},
    }

    PARAMS = (text_field("location", term=STREET),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street or village as the schedules on "
            "https://tkeliai.lt/atlieku-tvarkymas list it, e.g. 'Žalioji', "
            "'Butkų Juzės (nuo 1 iki 31)' or 'Paragai'. A street listed in "
            "several parts needs its house-number range; a village name that "
            "occurs in two elderships needs the eldership, e.g. 'Gintalai, "
            "Varnių seniūnija'. The old forms ('Žalioji g.', 'Butkų "
            "Juzės(1-31) g.', 'Paragai k.') keep working."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_INDEX_URL, pick=_both_pdfs),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(parsers.PdfTextParser(min_chars=500), then=_notices)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(type_value_map=_TYPES)
