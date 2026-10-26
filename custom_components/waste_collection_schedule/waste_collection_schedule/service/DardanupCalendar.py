"""Read the Shire's dated fiscal-year bin grids and street/service areas."""

from __future__ import annotations

import calendar
import datetime
import re
import statistics
from collections import defaultdict
from itertools import pairwise
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser, PdfWordLayoutParser
from waste_collection_schedule.service.ColourCellCalendar import classify_color

AREAS = {
    "Area 1": r"3-BIN SERVICES AREA 1",
    "Area 2": r"3-BIN SERVICES AREA 2",
    "Dardanup and Burekup": r"3-BIN SERVICE for Dardanup & Burekup",
    "Rural Area 1": r"2-BIN SERVICES - AREA 1",
    "Rural Area 2": r"2-BIN SERVICES - AREA 2",
}
_MONTHS = {
    name.upper(): index for index, name in enumerate(calendar.month_name) if name
}
_DAYS = {name.lower(): index for index, name in enumerate(calendar.day_name)}


def guide_urls(source, response):
    soup = BeautifulSoup(response.text, "html.parser")
    urls = list(
        dict.fromkeys(
            urljoin(response.url, str(a["href"]))
            for a in soup.select("a[href]")
            if re.search(r"waste[\s-]*guide", a.get_text(" ", strip=True), re.I)
            and ".pdf" in str(a["href"]).lower()
        )
    )
    if not urls:
        raise ValueError("Dardanup page has no published waste guide PDF")
    return urls


def _colour(value):
    # The guide uses cyan for cancelled days; its hue falls just below the
    # blue branch in the existing month-column colour classifier.
    if isinstance(value, (tuple, list)):
        if len(value) == 4:
            c, m, y, k = value
            rgb = ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
        elif len(value) == 3:
            rgb = value
        else:
            rgb = (0, 0, 0)
        r, g, b = rgb
        if b > r + 0.3 and g > r + 0.3:
            return "special"
    return classify_color(value)


def month_cells(layout, page):
    """Validate every printed day against its month, column and week row.

    Month headings supply both the year and the grid boundaries. Word centres
    and the last coloured vector covering each numeral supply the cell data.
    This also supports July-June grids, without a fixed year or PDF coordinate.
    """
    headings = []
    for line in layout.lines:
        if line.page != page:
            continue
        match = re.fullmatch(r"([A-Z]+)(20\d{2})", re.sub(r"\s", "", line.text.upper()))
        if match and match[1] in _MONTHS:
            headings.append((line, int(match[2]), _MONTHS[match[1]]))
    if len(headings) != 12 or len({(y, m) for _, y, m in headings}) != 12:
        raise ValueError("Expected twelve dated Dardanup month grids")
    dates = sorted(datetime.date(y, m, 1) for _, y, m in headings)
    if any(
        (b.year * 12 + b.month) - (a.year * 12 + a.month) != 1
        for a, b in pairwise(dates)
    ):
        raise ValueError("Dardanup calendar months are not consecutive")
    result = {}
    for heading, year, month in headings:
        neighbours = [h for h, _, _ in headings if abs(h.y - heading.y) < 3]
        pitch = min(
            abs(h.x - heading.x) for h in neighbours if abs(h.x - heading.x) > 3
        )
        lower = max((h.y for h, _, _ in headings if h.y < heading.y - 3), default=0)
        words = [
            w
            for w in layout.words
            if w.page == page
            and abs(w.x - heading.x) < pitch / 2
            and lower + 5 < w.y < heading.y - 7
            and re.fullmatch(r"\d{1,2}", w.text)
        ]
        by_day = defaultdict(list)
        for w in words:
            by_day[int(w.text)].append(w)
        expected = set(range(1, calendar.monthrange(year, month)[1] + 1))
        if set(by_day) != expected or any(len(ws) != 1 for ws in by_day.values()):
            raise ValueError(f"Incomplete printed Dardanup grid: {year}-{month:02}")
        columns = defaultdict(list)
        rows = defaultdict(list)
        first_weekday = datetime.date(year, month, 1).weekday()
        for day, ws in by_day.items():
            w = ws[0]
            date = datetime.date(year, month, day)
            columns[date.weekday()].append(w.x)
            rows[(first_weekday + day - 1) // 7].append(w.y)
            colours = [
                _colour(v.fill_color)
                for v in layout.vectors
                if v.page == page and v.x0 <= w.x <= v.x1 and v.y0 <= w.y <= v.y1
            ]
            marked = [c for c in colours if c is not None]
            result[date] = marked[-1] if marked else None
        xs = [statistics.median(columns[d]) for d in range(7)]
        if (
            xs != sorted(xs)
            or any(max(v) - min(v) > 2 for v in columns.values())
            or any(max(v) - min(v) > 2 for v in rows.values())
            or [statistics.median(v) for _, v in sorted(rows.items())]
            != sorted([statistics.median(v) for v in rows.values()], reverse=True)
        ):
            raise ValueError("Dardanup printed weekday/week positions changed")
    return result


def _street_area(html, street, selected):
    soup = BeautifulSoup(html, "html.parser")
    choices = []
    wanted = street.casefold().strip()
    for section in soup.select("div.accordion div.accordion"):
        heading = section.find_previous_sibling("h2")
        title = heading.get_text(" ", strip=True) if heading else ""
        area = next((a for a in ("Area 1", "Area 2") if a in title), None)
        day = None
        for child in section.children:
            if getattr(child, "name", None) == "h2":
                day = _DAYS.get(child.get_text(" ", strip=True).lower())
            elif getattr(child, "name", None) == "p" and area and day is not None:
                text = re.sub(r"\([^)]*\)", "", child.get_text(" ", strip=True))
                for name in re.split(r",| & ", text):
                    if wanted == name.strip().rstrip(".").casefold():
                        choices.append((area, day))
    choices = list(dict.fromkeys(choices))
    if selected:
        choices = [c for c in choices if c[0] == selected]
    if len(choices) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "service_area", street, [a for a, _ in choices]
        )
    return choices[0] if choices else (selected, None)


class CalendarParser(Parser[list[tuple[datetime.date, str]]]):
    def __call__(self, responses, source=None):
        if source is None:
            raise ValueError("Dardanup calendar requires a source")
        params = source.params
        if params.get("recycling_in_even_week") is not None:
            raise SourceArgumentRequired(
                "service_area",
                "Remove recycling_in_even_week and select the published service_area; ISO week parity does not remain valid across a 53-week year.",
            )
        area = params.get("service_area")
        street = params.get("street") or ""
        if area and area not in AREAS:
            raise SourceArgumentNotFoundWithSuggestions(
                "service_area", area, list(AREAS)
            )
        area, weekday = (
            _street_area(responses[0].text, street, area) if street else (area, None)
        )
        if not area:
            raise SourceArgumentRequired(
                "service_area",
                "Select the service area from the council waste guide; a weekday alone cannot identify the recycling route.",
            )
        requested_day = params.get("collection_day")
        if requested_day:
            weekday = _DAYS.get(requested_day.strip().lower())
            if weekday is None or weekday > 4:
                raise SourceArgumentNotFoundWithSuggestions(
                    "collection_day", requested_day, list(calendar.day_name)[:5]
                )
        today = datetime.date.today()
        result = set()
        covered = False
        for response in responses[1:]:
            layout = PdfWordLayoutParser(min_words=300, min_vectors=20)(
                response, source
            )[0]
            pages = {
                line.page
                for line in layout.lines
                if AREAS[area].casefold() in line.text.casefold()
            }
            if len(pages) != 1:
                raise ValueError(f"Could not find the published calendar for {area}")
            page = pages.pop()
            recycle_weekday = weekday
            page_text = " ".join(
                line.text for line in layout.lines if line.page == page
            )
            if (
                "No collection due to public holiday. Collection will take place the following day."
                not in page_text
            ):
                raise ValueError("Dardanup holiday replacement legend changed")
            if weekday is None and street:
                # The rural/townsite calendars print suburb-specific weekdays.
                lines = [line.text for line in layout.lines if line.page == page]
                found = [
                    m
                    for line in lines
                    if (
                        m := re.fullmatch(
                            r"(.+?)\s*\((Monday|Tuesday|Wednesday|Thursday|Friday)\)",
                            line,
                            re.I,
                        )
                    )
                    and street.casefold() in m[1].casefold()
                ]
                if len(found) == 1:
                    weekday = _DAYS[found[0][2].lower()]
                else:
                    split_days = [
                        m
                        for line in lines
                        if (
                            m := re.fullmatch(
                                r"(.+?)\s*\((Monday|Tuesday|Wednesday|Thursday|Friday) Waste, (Monday|Tuesday|Wednesday|Thursday|Friday) Recycle\)",
                                line,
                                re.I,
                            )
                        )
                        and street.casefold() in m[1].casefold()
                    ]
                    if len(split_days) == 1:
                        weekday = _DAYS[split_days[0][2].lower()]
                        recycle_weekday = _DAYS[split_days[0][3].lower()]
            if recycle_weekday is None:
                recycle_weekday = weekday
            if weekday is None:
                raise SourceArgumentRequired(
                    "collection_day",
                    "Enter the weekday shown for your street or townsite in the waste guide.",
                )
            cells = month_cells(layout, page)
            if min(cells) <= today <= max(cells):
                covered = True
            three_bins = not area.startswith("Rural")
            if three_bins and any(
                c not in ("general", "packaging", "special")
                for d, c in cells.items()
                if d.weekday() < 5
            ):
                raise ValueError(
                    "Dardanup three-bin calendar has unmarked collection weekdays"
                )
            for date, category in cells.items():
                if date.weekday() not in (weekday, recycle_weekday):
                    continue
                actual = date
                if category == "special":
                    actual += datetime.timedelta(days=1)
                    monday = date - datetime.timedelta(days=date.weekday())
                    week_colours = {
                        c
                        for d, c in cells.items()
                        if monday <= d < monday + datetime.timedelta(days=5)
                        and c in ("general", "packaging")
                    }
                    if len(week_colours) > 1 or (three_bins and not week_colours):
                        raise ValueError(
                            "Cannot determine bin types for a Dardanup holiday replacement"
                        )
                    category = week_colours.pop() if week_colours else None
                if not today <= actual < today + datetime.timedelta(weeks=26):
                    continue
                if three_bins:
                    result.add((actual, "organic"))
                    result.add(
                        (actual, "recycling" if category == "packaging" else "general")
                    )
                else:
                    if date.weekday() == weekday:
                        result.add((actual, "general"))
                    if category == "packaging" and date.weekday() == recycle_weekday:
                        result.add((actual, "recycling"))
        if not covered:
            raise ValueError("Dardanup has not published a waste guide covering today")
        return sorted(result)
