"""Brimbank City Council's colour-coded annual waste calendar (PDF).

The first page holds two year planners, calendar A (top) and calendar B
(bottom), each a grid of twelve mini month calendars (February to January).
Garbage is collected every week on the household's weekday; the weekday cells
of each week are filled yellow (recycling that week), green (food and garden
organics that week) or red (no collection, a public holiday). When Friday is a
holiday the week's Friday collection moves to the Saturday, which the PDF
colours as well.

The year and the months come from the printed month headings and every day
number is checked against its weekday column, so a changed layout fails loudly
instead of producing a wrong schedule.
"""

import calendar
import re
from collections.abc import Iterable
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = (
    "https://www.brimbank.vic.gov.au/living-here/my-home/"
    "rubbish-recycling-and-other-waste/bins"
)
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
_CALENDARS = ["A", "B"]

_GENERAL = "General Waste"
_RECYCLING = "Recycling"
_ORGANICS = "Food & Garden Organics"

#: Cell fills of the calendar (RGB) and what they mean.
_PALETTE = {
    (0.584, 0.795, 0.392): _ORGANICS,
    (1.0, 0.888, 0.312): _RECYCLING,
    (0.818, 0.408, 0.361): None,  # no collection (public holiday)
}
_TOLERANCE = 0.05
_HEADING_RE = re.compile(r"([^\W\d_]+)\s+(20\d{2})")


def calendar_link(response, *_keys, **_params) -> str:
    """The calendar PDF: the link whose text mentions the waste calendar."""
    from urllib.parse import urljoin

    for link in parsers.HtmlParser("a[href]")(response):
        if re.search(r"waste\s+calendar", link.get_text(" ", strip=True), re.I):
            return urljoin(str(response.url), str(link["href"]))
    raise response_shape.ResponseShapeError(
        "Brimbank City Council: no waste calendar link on the bins page"
    )


def _nearest_colour(fill: tuple[float, ...] | None) -> tuple[bool, str | None]:
    """(is a calendar colour, label) of a vector fill."""
    if fill is None or len(fill) != 3:
        return False, None
    for known, label in _PALETTE.items():
        dist = sum((a - b) ** 2 for a, b in zip(fill, known, strict=True)) ** 0.5
        if dist <= _TOLERANCE:
            return True, label
    return False, None


def _cell_labels(
    layout: parsers.PdfWordLayout, calendar_name: str, source: BaseSource
) -> dict[date, str | None]:
    """Date -> label (recycling / organics / None = no collection) for a calendar."""
    name = response_shape.source_name(source)

    def expect(condition, detail):
        response_shape.expect(
            condition, source_name=name, detail=detail, raw=str(layout.lines[:10])
        )

    headings = []
    for line in layout.lines:
        match = _HEADING_RE.fullmatch(line.text)
        if match and (month := recurrence.month(match.group(1))) is not None:
            headings.append((line, month, int(match.group(2))))
    expect(len(headings) == 24, "expected two calendars of twelve month grids")
    # A is the upper calendar: its twelve headings come first (top to bottom).
    ordered = sorted(headings, key=lambda h: -h[0].y)
    chosen = ordered[:12] if calendar_name == "A" else ordered[12:]

    cells = []
    for vector in layout.vectors:
        is_colour, label = _nearest_colour(vector.fill_color)
        if is_colour and 6 < vector.x1 - vector.x0 < 16:
            cells.append((vector, label))

    out: dict[date, str | None] = {}
    for heading, month, year in chosen:
        below = [
            line
            for line in layout.lines
            if line.text == "S M T W T F S"
            and line.page == heading.page
            and abs(line.x - heading.x) < 20
            and 0 < heading.y - line.y < 20
        ]
        expect(len(below) == 1, f"weekday header missing for {heading.text}")
        header = below[0]
        columns = sorted(
            (
                w
                for w in layout.words
                if w.page == header.page
                and abs(w.y - header.y) < 2
                and abs(w.x - header.x) < 38
            ),
            key=lambda w: w.x,
        )
        expect("".join(w.text for w in columns) == "SMTWTFS", "weekday header changed")
        step = (columns[-1].x - columns[0].x) / 6
        left, right = columns[0].x - step / 2, columns[-1].x + step / 2
        # Day rows end where the next month heading (or the page) begins.
        lower = max(
            (
                other.y
                for other, _m, _y in headings
                if other.page == heading.page
                and abs(other.x - heading.x) < 20
                and other.y < heading.y - 5
            ),
            # a month has at most six week rows of about 11 pt each
            default=header.y - 75,
        )
        days = [
            w
            for w in layout.words
            if w.page == header.page
            and w.text.isdigit()
            and left < w.x < right
            and lower < w.y < header.y - 2
        ]
        expect(bool(days), f"no days found in {heading.text}")
        # The first week row also prints the previous month's last days and, for
        # a month needing a sixth row, the month's own 29th-31st (Sunday/Monday
        # cells); the last row may show the next month's days.
        row_ys = sorted({round(w.y) for w in days}, reverse=True)
        seen: set[int] = set()
        for word in days:
            day = int(word.text)
            row = row_ys.index(round(word.y))
            column = min(range(7), key=lambda i: abs(columns[i].x - word.x))
            in_month = day <= calendar.monthrange(year, month)[1]
            weekday_ok = (
                in_month and date(year, month, day).weekday() == (column + 6) % 7
            )
            if (row == 0 and day > 7 and not (day > 28 and weekday_ok)) or (
                row == len(row_ys) - 1 and row > 0 and day <= 7
            ):
                continue
            expect(
                1 <= day <= calendar.monthrange(year, month)[1] and day not in seen,
                f"invalid or duplicate day in {heading.text}",
            )
            seen.add(day)
            when = date(year, month, day)
            expect(
                when.weekday() == (column + 6) % 7,
                f"date is in the wrong weekday column: {when}",
            )
            for vector, label in cells:
                if (
                    vector.page == word.page
                    and vector.x0 < word.x < vector.x1
                    and vector.y0 < word.y < vector.y1
                ):
                    out[when] = label
                    break
        expect(
            len(seen) == calendar.monthrange(year, month)[1],
            f"incomplete grid for {heading.text}",
        )
    return out


def _collection_rows(
    layouts: list[parsers.PdfWordLayout], source: BaseSource
) -> Iterable[tuple[date, str]]:
    day = str(source.params["day"]).strip().title()
    if day not in _DAYS:
        raise SourceArgumentNotFoundWithSuggestions("day", day, _DAYS)
    calendar_name = str(source.params["calendar"]).strip().upper()
    if calendar_name not in _CALENDARS:
        raise SourceArgumentNotFoundWithSuggestions(
            "calendar", calendar_name, _CALENDARS
        )
    weekday = _DAYS.index(day)

    cells = _cell_labels(layouts[0], calendar_name, source)
    for when, label in sorted(cells.items()):
        regular = when.weekday() == weekday and label is not None
        # A holiday Friday moves the Friday collection to the (coloured) Saturday.
        moved = (
            weekday == 4
            and when.weekday() == 5
            and label is not None
            and when - timedelta(days=1) in cells
            and cells[when - timedelta(days=1)] is None
        )
        if not regular and not moved:
            continue
        yield when, _GENERAL
        yield when, label


@final
class Source(BaseSource):
    TITLE = "Brimbank City Council"
    DESCRIPTION = "Source for Brimbank City Council waste collection."
    URL = "https://www.brimbank.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]
    TEST_CASES: ClassVar[dict] = {
        "Monday A": {"day": "Monday", "calendar": "A"},
        "Friday B": {"day": "Friday", "calendar": "B"},
        "Wednesday A": {"day": "Wednesday", "calendar": "A"},
    }
    PARAMS = (
        dropdown("day", _DAYS, label="Collection day"),
        dropdown("calendar", _CALENDARS, label="Calendar cycle"),
    )
    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Your collection day (Monday to Friday) and calendar cycle (A or B) are "
            "shown on the map on the back of the council's waste calendar PDF "
            "(linked from https://www.brimbank.vic.gov.au/living-here/my-home/"
            "rubbish-recycling-and-other-waste/bins)."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(retrievers.Lookup(_INDEX_URL, pick=calendar_link),),
        url=lambda *keys, **_: keys[-1],
    )
    parse = parsers.PdfWordLayoutParser(min_words=366, min_vectors=1)
    preprocess = staticmethod(_collection_rows)
    transform = ICSTransformer(
        type_value_map={
            _GENERAL: wt.GENERAL_WASTE,
            _RECYCLING: wt.RECYCLABLES,
            _ORGANICS: wt.ORGANIC,
        }
    )
