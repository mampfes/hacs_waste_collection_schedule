"""ZUK Oświęcim, Gmina Oświęcim, Poland (detached houses).

ZUK publishes one yearly PDF for Gmina Oświęcim's detached houses
(zabudowa jednorodzinna), linked from https://zuk.oswiecim.pl/harmonogramy.
The file is an Excel table: one row per collection region (Rejon I, II, ...),
the region's villages and streets in the second column, and a column per month
(Roman numerals) with the collection days ("11 25", "1, 15 29", "16* 20").
Page 1 is mixed waste. Page 2 is segregated waste (paper, plastics and metal,
glass on the same day) with the bulky-waste day marked "*", then a kitchen
bio-waste table for every street. The regions are not the same on both pages,
so a street is matched in each table on its own.

Other ZUK municipalities on the same index use different PDF layouts and are
not read here. The town of Oświęcim is served by a different company.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, ClassVar, NamedTuple, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import (
    lookups,
    parsers,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.PdfRuledTable import (
    RuledTableParser,
    RuledTables,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = "https://zuk.oswiecim.pl/harmonogramy"

_MIXED = "Odpady zmieszane"
_PAPER = "Papier i tektura"
_PLASTIC = "Tworzywa sztuczne i metale"
_GLASS = "Szkło"
_BULKY = "Odpady wielkogabarytowe"
_BIO = "Bioodpady"

_TYPES = {
    _MIXED: wt.GENERAL_WASTE,
    _PAPER: wt.PAPER,
    _PLASTIC: wt.RECYCLABLES,
    _GLASS: wt.GLASS,
    _BULKY: wt.BULKY_WASTE,
    _BIO: wt.ORGANIC,
}

# "BROSZKOWICE:" / "STAWY GROJECKIE:" — village names are printed in capitals.
_VILLAGE = re.compile(r"([A-ZĄĆĘŁŃÓŚŹŻ]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ]+)*)\s*:\s*")
_DAY = re.compile(r"(\d{1,2})\s*(\*)?")
_BEZ_RANGE = re.compile(
    r"^(?P<name>.*?)\s*\(\s*bez\s+nr\s+(?P<lo>\d+)\s*-\s*(?P<hi>\d+)\s*\)\s*$",
    re.IGNORECASE,
)
_ONLY_RANGE = re.compile(
    r"^(?P<name>.*?)\s+nr\s+(?P<lo>\d+)\s*-\s*(?P<hi>\d+)\s*$",
    re.IGNORECASE,
)
# "Gen. Andersa", "Św. Floriana", "Por. Króla" — the title is optional to type.
_TITLE = re.compile(r"^(?:ul|gen|por|św|sw|pl|ks)\.?\s+", re.IGNORECASE)


class _Street(NamedTuple):
    village: str
    name: str
    lo: int | None
    hi: int | None
    excluded: bool
    whole: bool
    dates: tuple[tuple[datetime.date, str], ...]


def _articles(response: Any, **_: Any) -> list[str]:
    """Detached-house schedule articles for Gmina Oświęcim, this year on."""
    found: dict[int, str] = {}
    for link in BeautifulSoup(response.text, "html.parser").find_all("a", href=True):
        text = " ".join(link.get_text(" ", strip=True).split())
        norm = lookups.normalize_loose(text)
        if "gmina oswiecim" not in norm or "jednorodzinna" not in norm:
            continue
        if "wielorodzinna" in norm:
            continue
        year = re.search(r"20\d\d", text)
        if year is None:
            continue
        found.setdefault(
            int(year.group()), urljoin(str(response.url), str(link["href"]))
        )
    response_shape.expect(
        bool(found),
        source_name="gmina_oswiecim_pl",
        detail="no Gmina Oświęcim detached-house schedule linked from the index",
        raw=response.text[:500],
    )
    current = datetime.date.today().year
    chosen = [year for year in sorted(found) if year >= current] or [max(found)]
    return [found[year] for year in chosen]


def _pdf(response: Any, *_keys: Any, **_: Any) -> str:
    """The schedule PDF linked from an article page."""
    hrefs: list[str] = []
    for link in BeautifulSoup(response.text, "html.parser").find_all("a", href=True):
        href = str(link["href"])
        if ".pdf" not in href.lower():
            continue
        absolute = urljoin(str(response.url), href)
        if absolute not in hrefs and "informacja" not in absolute.lower():
            hrefs.append(absolute)
    response_shape.expect(
        len(hrefs) == 1,
        source_name="gmina_oswiecim_pl",
        detail=f"expected one schedule PDF on the article, found {hrefs}",
        raw=response.text[:500],
    )
    return hrefs[0]


def _display(name: str) -> str:
    return name.title() if name.isupper() else name


def _same_name(wanted: str, printed: str) -> bool:
    """Equal names, or one clipped by a single repeated letter at the cell edge.

    The ruled-table reader drops a glyph whose centre falls on the border, so
    "Radziwiłł" can come out as "Radziwił". A one-letter difference counts only
    when it repeats the previous letter, which does not treat "Nowa" as "Nowak".
    """
    if wanted == printed:
        return True
    longer, shorter = (
        (wanted, printed) if len(wanted) > len(printed) else (printed, wanted)
    )
    return (
        len(longer) == len(shorter) + 1
        and longer.startswith(shorter)
        and longer[-1] == longer[-2]
    )


def _names(token: str) -> set[str]:
    full = lookups.normalize_loose(token)
    bare = lookups.normalize_loose(_TITLE.sub("", token))
    return {name for name in (full, bare) if name}


def _is_whole(token: str) -> bool:
    return "wszystkie ulice" in lookups.normalize_loose(token)


def _rule(token: str) -> tuple[str, int | None, int | None, bool]:
    """Street name plus an optional house-number range (included or excluded)."""
    match = _BEZ_RANGE.match(token) or _ONLY_RANGE.match(token)
    if match is None:
        return token, None, None, False
    return (
        match.group("name").strip(),
        int(match.group("lo")),
        int(match.group("hi")),
        match.re is _BEZ_RANGE,
    )


def _segments(cell: str) -> list[tuple[str, list[str]]]:
    """``(village, street tokens)`` from one region's street cell."""
    # The segregated table prints "Ofiar Faszymu" for Ofiar Faszyzmu.
    cell = re.sub(r"(?i)faszymu", "Faszyzmu", cell)
    villages = list(_VILLAGE.finditer(cell))
    if not villages:
        if not _is_whole(cell):
            return []
        body = re.sub(r"(?i)\s*-\s*wszystkie ulice.*$", "", cell)
        return [
            (name.strip(), ["Całość (wszystkie ulice)"])
            for name in body.split(",")
            if name.strip()
        ]
    segments: list[tuple[str, list[str]]] = []
    for index, village in enumerate(villages):
        end = villages[index + 1].start() if index + 1 < len(villages) else len(cell)
        tokens = [
            token.strip(" .")
            for token in cell[village.end() : end].split(",")
            if token.strip(" .")
        ]
        if tokens:
            segments.append((village.group(1).strip(), tokens))
    return segments


def _header_months(row: list[str]) -> dict[int, int] | None:
    if lookups.normalize_loose(row[0]) != "rejon":
        return None
    months = {
        index: month
        for index, cell in enumerate(row)
        if (month := recurrence.month(cell.strip(), roman=True))
    }
    if len(set(months.values())) != 12:
        return None
    return months


def _labels(mode: str, starred: bool) -> tuple[str, ...]:
    if mode == "mixed":
        return (_MIXED,)
    if mode == "bio":
        return (_BIO,)
    # "*" is the bulky day printed in the segregated table's legend.
    return (_BULKY,) if starred else (_PAPER, _PLASTIC, _GLASS)


def _number_ok(house: str | None, street: _Street) -> bool | None:
    """Whether ``house`` is served by ``street``. None: a number is required."""
    if street.lo is None or street.hi is None:
        return True
    if not house:
        return None
    match = re.match(r"\d+", house.strip())
    if match is None:
        return False
    number = int(match.group())
    inside = street.lo <= number <= street.hi
    return not inside if street.excluded else inside


def _example(street: _Street) -> str:
    if street.lo is None or street.hi is None:
        return "1"
    if street.excluded:
        return str(street.lo - 1 if street.lo > 1 else street.hi + 1)
    return str(street.lo)


def _rows_of(document: RuledTables, source: BaseSource | None) -> list[_Street]:
    """One entry per street (or whole village) in this PDF, with its dates."""
    name = response_shape.source_name(source)
    years = {
        int(year)
        for year in re.findall(
            r"Harmonogram odbierania odpadów\s+(20\d\d)", document.text
        )
    }
    response_shape.expect(
        len(years) == 1,
        source_name=name,
        detail=f"expected one schedule year, found {sorted(years)}",
        raw=document.text[:500],
    )
    year = next(iter(years))
    rows: list[_Street] = []
    seen: set[str] = set()
    for grid in document.grids:
        months: dict[int, int] | None = None
        mode: str | None = None
        for row in grid:
            header = _header_months(row)
            if header is not None:
                months = header
                continue
            if "bioodpady" in lookups.normalize_loose(" ".join(row)):
                mode = "bio"
                continue
            if (
                months is None
                or recurrence.roman(row[0].strip()) is None
                or not row[1].strip()
            ):
                continue
            if mode is None:
                mode = (
                    "segregated"
                    if any("*" in row[index] for index in months)
                    else "mixed"
                )
            seen.add(mode)
            dates: list[tuple[datetime.date, str]] = []
            for index, month in months.items():
                for day, star in _DAY.findall(row[index]):
                    try:
                        collection = datetime.date(year, month, int(day))
                    except ValueError:
                        response_shape.expect(
                            False,
                            source_name=name,
                            detail=f"day {day} is not in month {month} ({row[index]!r})",
                        )
                        continue
                    dates.extend(
                        (collection, label) for label in _labels(mode, bool(star))
                    )
            stamped = tuple(sorted(set(dates)))
            for village, tokens in _segments(row[1]):
                for token in tokens:
                    whole = _is_whole(token)
                    street_name, lo, hi, excluded = (
                        ("", None, None, False) if whole else _rule(token)
                    )
                    rows.append(
                        _Street(
                            _display(village),
                            _display(street_name)
                            if street_name.isupper()
                            else street_name,
                            lo,
                            hi,
                            excluded,
                            whole,
                            stamped,
                        )
                    )
    response_shape.expect(
        seen == {"mixed", "segregated", "bio"},
        source_name=name,
        detail=f"schedule sections {sorted(seen)} (expected mixed, segregated, bio)",
        raw=document.text[:500],
    )
    return rows


def _section(street: _Street) -> str:
    labels = {label for _, label in street.dates}
    if _MIXED in labels:
        return "mixed"
    if _BIO in labels:
        return "bio"
    return "segregated"


def _select(
    streets: list[_Street], source: BaseSource | None
) -> list[tuple[datetime.date, str]]:
    """The configured village and street, matched separately in each section.

    Mixed, segregated and bio-waste regions are not the same list, and a
    village published as "Całość (wszystkie ulice)" matches any street only
    where that section gives no explicit list.
    """
    params = source.params if source else {}
    village = lookups.normalize_loose(params.get("city") or "")
    wanted = _names(str(params.get("street") or ""))
    house = (
        str(params.get("house_number")).strip() if params.get("house_number") else None
    )

    villages = sorted({item.village for item in streets})
    in_village = [
        item for item in streets if lookups.normalize_loose(item.village) == village
    ]
    if not in_village:
        raise SourceArgumentNotFoundWithSuggestions(
            "city", params.get("city"), villages
        )

    names = sorted({item.name for item in in_village if item.name and not item.whole})
    sections: dict[str, list[_Street]] = {}
    for item in in_village:
        sections.setdefault(_section(item), []).append(item)

    chosen: list[tuple[datetime.date, str]] = []
    pending: list[_Street] = []
    missed = False
    bad_number: list[_Street] = []
    for places in sections.values():
        # One PDF is one year. Resolve each year on its own so fetching this
        # year and the next together unions the dates, instead of looking like
        # two regions for the same street.
        years = sorted({item.dates[0][0].year if item.dates else 0 for item in places})
        for year in years:
            year_places = [
                item
                for item in places
                if (item.dates[0][0].year if item.dates else 0) == year
            ]
            hits = [
                item
                for item in year_places
                if not item.whole and wanted & _names(item.name)
            ]
            if hits:
                decided: list[_Street] = []
                for item in hits:
                    ok = _number_ok(house, item)
                    if ok is None:
                        pending.append(item)
                    elif ok:
                        decided.append(item)
                    else:
                        bad_number.append(item)
                signatures = {item.dates for item in decided}
                if len(signatures) > 1:
                    raise SourceArgAmbiguousWithSuggestions(
                        "street", params.get("street"), names
                    )
                if signatures:
                    chosen.extend(next(iter(signatures)))
                elif not any(_number_ok(house, item) is None for item in hits):
                    missed = True
                continue
            # "Całość" matches any street only where this section lists none.
            if any(not item.whole for item in year_places):
                missed = True
                continue
            chosen.extend(next(item.dates for item in year_places if item.whole))
    if pending:
        raise SourceArgAmbiguousWithSuggestions(
            "house_number",
            house or "",
            sorted({_example(item) for item in pending}),
        )
    if missed or not chosen:
        if bad_number and house:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number",
                house,
                sorted({_example(item) for item in bad_number}),
            )
        raise SourceArgumentNotFoundWithSuggestions(
            "street", params.get("street"), names
        )
    return sorted(set(chosen))


@final
class Source(BaseSource):
    TITLE = "Gmina Oświęcim"
    DESCRIPTION = "Source for ZUK Oświęcim waste collection in Gmina Oświęcim, Poland."
    URL = "https://zuk.oswiecim.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.BULKY_WASTE,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Brzezinka, Niwy": {"city": "Brzezinka", "street": "Niwy"},
        "Brzezinka, Ofiar Faszyzmu 16": {
            "city": "Brzezinka",
            "street": "Ofiar Faszyzmu",
            "house_number": "16",
        },
    }

    PARAMS = (
        city("city"),
        street("street"),
        house_number("house_number", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "On https://zuk.oswiecim.pl/harmonogramy open the Gmina Oświęcim "
            "schedule for detached houses (zabudowa jednorodzinna). Enter your "
            "village (sołectwo, e.g. 'Brzezinka') and your street as printed "
            "there (e.g. 'Niwy'). Ofiar Faszyzmu is split by house number: "
            "14-18 is a separate mixed-waste round, so enter the house number "
            "too. Bulky waste and kitchen bio-waste are collected on the "
            "printed days only after you book them with ZUK. Multi-family "
            "buildings and the town of Oświęcim are not covered."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_INDEX_URL, pick=_articles),
        targets=lambda source, articles: articles,
        fetch=retrievers.Request(
            lambda article, articles, pdf, **_: pdf,
            before=(
                retrievers.Lookup(
                    lambda article, articles, **_: article,
                    pick=_pdf,
                ),
            ),
        ),
    )
    parse = parsers.EachResponse(
        RuledTableParser(min_cells=80),
        then=_rows_of,
    )
    preprocess = staticmethod(_select)
    transform = ICSTransformer(type_value_map=_TYPES)
