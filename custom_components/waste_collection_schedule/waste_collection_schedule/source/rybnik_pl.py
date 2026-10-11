"""Rybnik, Poland (EKO Sp. z o.o.).

The city publishes its schedules as PDFs under a per-year folder:

* residential and commercial properties: one PDF per district group. Page 1
  lists the zones (Rejon) of the group with their streets; the schedule page
  prints one block per zone (a row per round, a column per month, the days in
  each cell) in the same order, and a footer with the bulky-waste dates.
* multifamily housing: one city-wide PDF with a ruled table whose cells hold
  weekday rules ("środa tydzień nieparzysty"), expanded here over the year.

The current year's PDF is tried first, then the previous year's.
"""

import re
from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import (
    date_parsers,
    lookups,
    parsers,
    preprocessors,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    district,
    dropdown,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.PdfRuledTable import (
    RuledTableParser,
    RuledTables,
    merge_split_rows,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = (
    "https://www.rybnik.eu/fileadmin/user_files/mieszkaj/samorzad/"
    "odpady_komunalne/Harmonogramy_{year}/"
)

# district -> slug in the PDF file name, the zones (Rejon) of its cover table in
# the order of the schedule blocks, and aliases where the footer abbreviates one.
DISTRICT_MAP: dict[str, dict] = {
    "Boguszowice Stare": {
        "slug": "Boguszowice_Stare",
        "zones": [f"Boguszowice Stare {i}" for i in range(1, 6)],
    },
    "Chwalowice / Boguszowice Os. / Klokocin": {
        "slug": "Chwalowice__Boguszowice_Os.__Klokocin",
        "zones": [
            "Chwałowice 1",
            "Chwałowice 2",
            "Boguszowice Osiedle",
            "Kłokocin 1",
            "Kłokocin 2",
        ],
    },
    "Gotartowice": {
        "slug": "Gotartowice",
        "zones": [f"Gotartowice {i}" for i in range(1, 5)],
    },
    "Grabownia / Golejow / Ochojec": {
        "slug": "Grabownia__Golejow__Ochojec",
        "zones": ["Grabownia", "Golejów 1", "Golejów 2", "Ochojec 1", "Ochojec 2"],
    },
    "Ligota": {
        "slug": "Ligota",
        "zones": [f"Ligota-Ligocka Kuźnia {i}" for i in range(1, 5)],
    },
    "Maroko-Nowiny": {
        "slug": "Maroko-Nowiny",
        "zones": [f"Maroko-Nowiny {i}" for i in range(1, 7)],
    },
    "Niedobczyce": {
        "slug": "Niedobczyce",
        "zones": [f"Niedobczyce {i}" for i in range(1, 8)],
    },
    "Niewiadom": {
        "slug": "Niewiadom",
        "zones": [f"Niewiadom {i}" for i in range(1, 5)],
    },
    "Orzepowice / Stodoly / Chwalecice": {
        "slug": "Orzepowice__Stodoly__Chwalecice",
        "zones": [
            "Orzepowice 1",
            "Orzepowice 2",
            "Stodoły",
            "Chwałęcice 1",
            "Chwałęcice 2",
        ],
    },
    "Paruszowiec / Kamien": {
        "slug": "Paruszowiec__Kamien",
        "zones": ["Paruszowiec-Piaski", "Kamień 1", "Kamień 2"],
    },
    "Polnoc": {
        "slug": "Polnoc",
        "zones": [f"Rybnik-Północ {i}" for i in range(1, 6)],
    },
    "Radziejow / Popielow": {
        "slug": "Radziejow__Popielow",
        "zones": ["Radziejów", "Popielów 1", "Popielów 2", "Popielów 3"],
    },
    "Smolna / Zamyslow / Meksyk": {
        "slug": "Smolna__Zamyslow__Meksyk",
        "zones": [
            "Smolna 1",
            "Smolna 2",
            "Zamysłów 1",
            "Zamysłów 2",
            "Zamysłów 3",
            "Meksyk",
        ],
    },
    "Srodmiescie / Wielopole / Kuznia": {
        "slug": "Srodmiescie__Wielopole__Kuznia",
        "zones": [
            "Śródmieście 1",
            "Śródmieście 2",
            "Wielopole 1",
            "Wielopole 2",
            "Kuźnia Rybnicka",
        ],
        "zone_aliases": {"Kuźnia Rybnicka": ["Kuźnia"]},
    },
    "Zebrzydowice": {
        "slug": "Zebrzydowice",
        "zones": [f"Zebrzydowice {i}" for i in range(1, 5)],
    },
}

PROPERTY_TYPES = ["residential", "commercial", "multifamily"]

# The round labels as printed (residential rows and multifamily column headings).
_TYPES = {
    "ZMIESZANE": wt.GENERAL_WASTE,
    "SEGREGOWANE": wt.RECYCLABLES,
    "BIODEGRADOWALNE": wt.ORGANIC,
    "GABARYTY": wt.BULKY_WASTE,
    "PLASTIK": wt.PLASTIC,
    "PAPIER": wt.PAPER,
    "SZKŁO": wt.GLASS,
    "WIELKOGABARYTY": wt.BULKY_WASTE,
    "BIO": wt.ORGANIC,
    # Ash is a winter-only round printed with dashes; not surfaced.
    "POPIOŁY/ŻUŻEL": None,
}

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


# --- retrieval (pure request shaping) -------------------------------------


def _candidate_years(**_: Any) -> list[int]:
    today = date.today()
    return [today.year, today.year - 1]


def _pdf_url(
    candidate: int, *, property_type: str, district: str | None, **_: Any
) -> str:
    base = _BASE_URL.format(year=candidate)
    if property_type == "multifamily":
        return f"{base}Wielorodzinna_{candidate}.pdf"
    if not district:
        raise SourceArgumentRequiredWithSuggestions(
            "district", "district is required", list(DISTRICT_MAP)
        )
    slug = lookups.resolve(DISTRICT_MAP, district, argument="district")["slug"]
    if property_type == "commercial":
        return f"{base}Firmy{candidate}_{slug}_firmy_{candidate}.pdf"
    return f"{base}zamieszkale{candidate}_{slug}_{candidate}.pdf"


def _is_pdf(response: Any) -> bool:
    return response.status_code == 200 and response.content[:4] == b"%PDF"


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
            if _TYPES[key] is None:
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


def _rows_of(grid: list[list[str]]) -> list[tuple[str, list[str], dict[str, str]]]:
    """``(area, streets, {round: rule})`` rows of one multifamily table."""
    header = None
    columns: dict[int, str] = {}
    for r, cols in enumerate(grid):
        found = {
            c: key
            for c, cell in enumerate(cols)
            for key in _MULTIFAMILY_TYPES
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


@final
class Source(BaseSource):
    TITLE = "Rybnik"
    DESCRIPTION = (
        "Source for Rybnik (Poland) municipal waste collection schedules "
        "provided by EKO Sp. z o.o."
    )
    URL = "https://www.rybnik.eu"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.BULKY_WASTE,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Paruszowiec-Piaski residential": {
            "district": "Paruszowiec / Kamien",
            "sub_district": "Paruszowiec-Piaski",
            "property_type": "residential",
        },
        "Boguszowice Stare residential (all sub-districts)": {
            "district": "Boguszowice Stare",
            "property_type": "residential",
        },
        "Niedobczyce commercial": {
            "district": "Niedobczyce",
            "property_type": "commercial",
        },
        "Zebrzydowice 1 residential": {
            "district": "Zebrzydowice",
            "sub_district": "Zebrzydowice 1",
            "property_type": "residential",
        },
        "Multifamily Rudzka, Stodoły (odd/even weeks)": {
            "property_type": "multifamily",
            "street": "Rudzka",
            "sub_district": "Stodoły",
        },
        "Multifamily Chabrowa (Maroko-Nowiny)": {
            "property_type": "multifamily",
            "street": "Chabrowa",
        },
    }

    PARAMS = (
        district("district", optional=True),
        text_field("sub_district", "Sub-district (Rejon)", optional=True),
        dropdown(
            "property_type",
            PROPERTY_TYPES,
            label="Property type",
            default="residential",
        ),
        street("street", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose the property type: 'residential' (zamieszkałe), 'commercial' "
            "(firmy/niezamieszkałe) or 'multifamily' (zabudowa wielorodzinna). "
            "For residential and commercial properties enter the district group "
            "(e.g. 'Paruszowiec / Kamien') and optionally the Rejon (zone) from the "
            "left column of the PDF cover table (e.g. 'Kamień 1'); leave it blank "
            "for all zones of the district. The PDFs are on "
            "https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne/. For multifamily "
            "housing enter your street as listed in the 'ULICE' column, and the "
            "'DZIELNICA' value (e.g. 'Stodoły') as sub-district if the street is "
            "listed for several areas."
        ),
    }

    retrieve = retrievers.FirstMatchRetriever(
        candidates=_candidate_years, url=_pdf_url, accept=_is_pdf
    )

    _TEXT = parsers.PdfTextParser(min_chars=200)
    _TABLE = RuledTableParser(min_cells=20)

    def parse(self, response: Any, source: Any) -> Any:
        if self.params["property_type"] == "multifamily":
            return self._TABLE(response, source)
        return self._TEXT(response, source)

    def preprocess(self, document: Any, source: Any = None) -> list:
        params = self.params
        if params["property_type"] == "multifamily":
            return self._multifamily(document, params)
        cfg = lookups.resolve(DISTRICT_MAP, params["district"], argument="district")
        return zone_rows(
            document,
            cfg["zones"],
            cfg.get("zone_aliases", {}),
            (params["sub_district"] or "").strip(),
        )

    def _multifamily(self, document: RuledTables, params: dict) -> list:
        street_name = (params["street"] or "").strip()
        area = (params["sub_district"] or "").strip()
        if not street_name and not area:
            raise SourceArgumentRequired(
                "street", "street is required for property_type 'multifamily'"
            )
        rows = [row for grid in document.grids for row in _rows_of(grid)]
        response_shape.expect(
            bool(rows),
            source_name="rybnik_pl",
            detail="no rows in the multifamily table",
            raw=document.text[:300],
        )
        _, _, rules = select_row(rows, street_name, area)
        year = _year_of(document.text)
        return list(preprocessors.RecurrenceExpander(_schedules)([(year, rules)]))

    transform = ICSTransformer(type_value_map=_TYPES)
