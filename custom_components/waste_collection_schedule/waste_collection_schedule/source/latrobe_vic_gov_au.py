"""Latrobe City Council (VIC) kerbside collections.

Two public sources are combined:

* The council's property layer on ArcGIS Online names each serviced
  property's collection weekday ("Wednesday") and calendar area ("Area A" or
  "Area B").
* The council's recycling and green waste calendar PDF, linked from the bin
  collection page, has one set of mini month grids per area. The weekday cells
  of every week are painted yellow (mixed recycling that week) or green (food
  and garden organics that week); general rubbish goes out every week.

The calendar's years come from its title ("JULY 2026 TO JUNE 2027", or a
single year with "JANUARY TO JUNE") and every printed day is checked against
its weekday column, so a changed layout fails loudly rather than shifting the
schedule. The cells are painted partly as filled rectangles and partly as
thick stroked lines, so the PDF is read with ``include_strokes``.
"""

import calendar
import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta
from typing import ClassVar, final
from urllib.parse import urlencode, urljoin

from waste_collection_schedule import parsers, recurrence, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
)
from waste_collection_schedule.service.ArcGis import (
    ArcGisDistinctValues,
    ArcGisFeatureParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_BIN_PAGE = "https://www.latrobe.vic.gov.au/Home/Waste/Bin_Collection"
_LAYER = (
    "https://services-ap1.arcgis.com/AtixmNNZDz8cwc9l/arcgis/rest/services/"
    "PathwayProperty%20View/FeatureServer/0"
)
_FIELDS = "Property_A,Suburb,Waste_Coll,Waste_Firs"

_GENERAL = "General Rubbish"
_RECYCLING = "Mixed Recycling"
_FOGO = "Food and Garden Organics"

#: The calendar's cell paints (CMYK as printed) and what they mean.
_PALETTE = {
    (0.011, 0.154, 0.995, 0.0): _RECYCLING,
    (0.568, 0.0, 0.992, 0.0): _FOGO,
}
_TOLERANCE = 0.05
_WEEKDAY_HEADERS = {"SMTWTFS": 6, "MTWTFSS": 0}  # first column's weekday


def _sql(value: str) -> str:
    return " ".join(str(value).split()).upper().replace("'", "''")


def _where(address: str, suburb: str, **_) -> str:
    return f"UPPER(Property_A) = '{_sql(address)}' AND UPPER(Suburb) = '{_sql(suburb)}'"


def _similar(address: str, suburb: str, **_) -> str:
    """Addresses in the suburb on the same street, for a no-match suggestion."""
    words = [w for w in _sql(address).split() if not any(c.isdigit() for c in w)]
    street = f" AND UPPER(Property_A) LIKE '% {words[0]} %'" if words else ""
    return f"UPPER(Suburb) = '{_sql(suburb)}'{street}"


def _property_query(source: BaseSource) -> str:
    query = {
        "where": _where(**source.params),
        "outFields": _FIELDS,
        "returnGeometry": "false",
        "f": "json",
    }
    return f"{_LAYER}/query?{urlencode(query)}"


def _calendar_urls(response, **_) -> list[str]:
    """Every distinct calendar PDF linked as the "Waste Calendar"."""
    urls: list[str] = []
    for link in parsers.HtmlParser("a[href]")(response):
        href = urljoin(str(response.url), str(link["href"]))
        if (
            re.search(r"waste\s+calendar", link.get_text(" ", strip=True), re.I)
            and href.lower().endswith(".pdf")
            and href not in urls
        ):
            urls.append(href)
    response_shape.expect(
        bool(urls),
        source_name="Latrobe City Council",
        detail="no waste calendar link on the bin collection page",
        raw=response.text[:500],
    )
    return urls


def _label(colour: tuple[float, ...] | None) -> str | None:
    if colour is None:
        return None
    for known, label in _PALETTE.items():
        if len(colour) == len(known) and all(
            abs(a - b) <= _TOLERANCE for a, b in zip(colour, known, strict=True)
        ):
            return label
    return None


def _area_labels(layout: parsers.PdfWordLayout) -> list[tuple[str, float, float]]:
    """("A" or "B", x, y) of every printed "Area A" / "Area B" label.

    The label is either an ordinary line or set vertically, letter by letter,
    in which case it is spelt by the single letters sharing one column.
    """
    labels = []
    for line in layout.lines:
        if line.page == 0 and (match := re.match(r"Area ([AB])\b", line.text)):
            labels.append((match.group(1), line.x, line.y))
    columns = defaultdict(list)
    for word in layout.words:
        if word.page == 0 and len(word.text) == 1:
            columns[round(word.x)].append(word)
    for letters in columns.values():
        letters.sort(key=lambda w: w.y)
        spelt = "".join(w.text for w in letters)
        for match in re.finditer(r"Area([AB])", spelt):
            run = letters[match.start() : match.end()]
            labels.append((match.group(1), run[0].x, sum(w.y for w in run) / len(run)))
    return labels


def _area_calendars(
    layout: parsers.PdfWordLayout, source: BaseSource
) -> dict[str, dict[date, str | None]]:
    """Area -> {date: cell label (None for an unpainted cell)}."""
    name = response_shape.source_name(source)

    def expect(condition, detail):
        response_shape.expect(
            condition, source_name=name, detail=detail, raw=str(layout.lines[:10])
        )

    page = [line for line in layout.lines if line.page == 0]
    span = None
    for line in page:
        match = re.search(r"([A-Za-z]+)(?:\s+20\d\d)?\s+TO\s+([A-Za-z]+)", line.text)
        if (
            match
            and recurrence.month(match.group(1))
            and recurrence.month(match.group(2))
        ):
            span = recurrence.month(match.group(1))
    years = sorted(
        {int(y) for line in page for y in re.findall(r"\b(20\d\d)\b", line.text)}
    )
    expect(span is not None and bool(years), "calendar period not found in the title")
    first_year = years[0]

    labels = _area_labels(layout)
    expect(
        {area for area, _x, _y in labels} == {"A", "B"}, "Area A / B labels not found"
    )

    def distance(area, word):
        return min(
            ((x - word.x) ** 2 + (y - word.y) ** 2) ** 0.5
            for label, x, y in labels
            if label == area
        )

    # Every month is printed once per area: of its two headings, the one
    # relatively nearer an "Area A" label belongs to area A.
    headings = defaultdict(list)
    for line in page:
        if line.text.isalpha() and (month := recurrence.month(line.text)) is not None:
            headings[month].append(line)
    expect(
        len(headings) in (6, 12) and all(len(h) == 2 for h in headings.values()),
        "expected each month once per area",
    )
    grids = []
    for month, pair in headings.items():
        pair.sort(key=lambda w: distance("A", w) - distance("B", w))
        grids += [("A", month, pair[0]), ("B", month, pair[1])]

    letters = [w for w in layout.words if w.page == 0 and w.text in "SMTWF"]
    painted = [
        (v, _label(v.fill_color if v.fill_color is not None else v.stroke_color))
        for v in layout.vectors
        if v.page == 0 and v.x1 - v.x0 < 40 and v.y1 - v.y0 < 40
    ]
    result: dict[str, dict[date, str | None]] = {"A": {}, "B": {}}
    for area, month, heading in grids:
        year = first_year if month >= span else first_year + 1
        below = [w for w in letters if 0 < heading.y - w.y < 25]
        expect(bool(below), f"weekday header missing under {heading.text}")
        header_y = max(w.y for w in below)
        row = sorted((w for w in below if abs(w.y - header_y) < 1.5), key=lambda w: w.x)
        groups = [row[i : i + 7] for i in range(0, len(row), 7)]
        columns = min(groups, key=lambda g: abs((g[0].x + g[-1].x) / 2 - heading.x))
        header = "".join(w.text for w in columns)
        expect(header in _WEEKDAY_HEADERS, f"weekday header changed: {header}")
        first_weekday = _WEEKDAY_HEADERS[header]
        step = (columns[-1].x - columns[0].x) / 6
        left, right = columns[0].x - step / 2, columns[-1].x + step / 2
        lower = max(
            (
                other.y
                for lines in headings.values()
                for other in lines
                if left < other.x < right and other.y < header_y - 2
            ),
            default=header_y - 100,
        )
        last_day = calendar.monthrange(year, month)[1]
        previous = date(year, month, 1) - timedelta(days=1)
        cells: dict[date, str | None] = {}
        for word in layout.words:
            if not (
                word.page == 0
                and word.text.isdigit()
                and left < word.x < right
                and lower < word.y < header_y - 2
            ):
                continue
            day = int(word.text)
            column = min(range(7), key=lambda i: abs(columns[i].x - word.x))
            weekday = (first_weekday + column) % 7
            covering = [
                (v, label)
                for v, label in painted
                if v.x0 <= word.x <= v.x1 and v.y0 <= word.y <= v.y1
            ]
            label = (
                min(covering, key=lambda c: (c[0].x1 - c[0].x0) * (c[0].y1 - c[0].y0))[
                    1
                ]
                if covering
                else None
            )
            when = date(year, month, day) if day <= last_day else None
            if when is None or when.weekday() != weekday or when in cells:
                # The previous month's last days fill the first row of some
                # grids, and one unpainted Sunday cell is misprinted; anything
                # painted must date cleanly.
                spill = (
                    day <= previous.day
                    and previous.replace(day=day).weekday() == weekday
                )
                expect(label is None or spill, f"misplaced day {day} in {heading.text}")
                continue
            cells[when] = label
        workdays = {
            date(year, month, d)
            for d in range(1, last_day + 1)
            if date(year, month, d).weekday() < 5
        }
        expect(workdays <= set(cells), f"incomplete grid for {heading.text} {year}")
        result[area].update(cells)
    return result


def _collection_rows(records: list, source: BaseSource) -> Iterable[tuple[date, str]]:
    properties = [r for r in records if isinstance(r, dict)]
    layouts = [r for r in records if isinstance(r, parsers.PdfWordLayout)]
    services = {
        (str(p.get("Waste_Coll") or "").strip(), str(p.get("Waste_Firs") or "").strip())
        for p in properties
    } - {("", "")}
    if not services or any(not area or not day for area, day in services):
        raise SourceArgumentException(
            "address", "no kerbside collection area and day recorded for this property"
        )
    if len(services) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address",
            source.params["address"],
            sorted(f"{area}, {day}" for area, day in services),
        )
    area_name, day_name = services.pop()
    area_match = re.fullmatch(r"Area ([AB])", area_name)
    weekday = recurrence.weekday(day_name)
    if area_match is None or weekday is None or weekday > 4:
        raise SourceArgumentException(
            "address", f"unexpected collection area / day: {area_name}, {day_name}"
        )
    response_shape.expect(
        bool(layouts),
        source_name=response_shape.source_name(source),
        detail="no calendar PDF",
        raw="",
    )
    seen: set[tuple[date, str]] = set()
    for layout in layouts:
        cells = _area_calendars(layout, source)[area_match.group(1)]
        for when, label in sorted(cells.items()):
            if when.weekday() != weekday or label is None:
                continue
            for row in ((when, _GENERAL), (when, label)):
                if row not in seen:
                    seen.add(row)
                    yield row


@final
class Source(BaseSource):
    TITLE = "Latrobe City Council"
    DESCRIPTION = "Source for Latrobe City Council (VIC) kerbside collection."
    URL = "https://www.latrobe.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]
    TEST_CASES: ClassVar[dict] = {
        "23-25 Ann Street, Morwell": {
            "address": "23-25 Ann Street",
            "suburb": "Morwell",
        },
        "16 Hourigan Drive, Traralgon East": {
            "address": "16 Hourigan Drive",
            "suburb": "Traralgon East",
        },
        "95-97 Albert Street, Moe": {"address": "95-97 Albert Street", "suburb": "Moe"},
    }
    PARAMS = (street_address("address"), city("suburb"))
    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter the property address as on your rates notice, with the street "
            "type written out (e.g. 23-25 Ann Street), and the suburb (e.g. "
            "Morwell). The collection day and area (A or B) come from the "
            "council's property records and the dates from the council's "
            "recycling and green waste calendar PDF. The council's website only "
            "answers from Australian internet connections, so the source does "
            "not work through a VPN or proxy outside Australia."
        ),
        "de": (
            "Gib die Adresse wie auf dem Grundsteuerbescheid ein, mit "
            "ausgeschriebenem Straßentyp (z. B. 23-25 Ann Street), und den Ort "
            "(z. B. Morwell). Abholtag und Bereich (A oder B) stammen aus den "
            "Grundstücksdaten der Stadt, die Termine aus ihrem Abfallkalender "
            "(PDF). Die Website der Stadt antwortet nur aus australischen Netzen."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_BIN_PAGE, pick=_calendar_urls),
        targets=lambda source, urls: [_property_query(source), *urls],
        fetch=retrievers.Request(lambda url, _urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.ByBodyPrefix(
            {"%PDF-": parsers.PdfWordLayoutParser(min_words=300, include_strokes=True)},
            default=ArcGisFeatureParser(
                argument="address",
                suggestions=ArcGisDistinctValues(
                    _LAYER, "Property_A", where=_similar, limit=50
                ),
            ),
        )
    )
    preprocess = staticmethod(_collection_rows)
    transform = ICSTransformer(
        type_value_map={
            _GENERAL: wt.GENERAL_WASTE,
            _RECYCLING: wt.RECYCLABLES,
            _FOGO: wt.ORGANIC,
        }
    )
