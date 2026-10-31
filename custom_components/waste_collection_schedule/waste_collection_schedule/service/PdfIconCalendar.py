"""Read dated month grids whose bin symbols are embedded raster images.

Templates come from the document's own labelled legend. Matching uses small
RGB thumbnails and aspect ratios, allowing a PDF to reuse a downscaled version
of a legend image in its cells. Vector artwork is not a collection symbol here.
"""

from __future__ import annotations

import calendar
import datetime
import re
from collections import defaultdict
from io import BytesIO
from itertools import pairwise
from statistics import median
from typing import NamedTuple

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser


class Word(NamedTuple):
    text: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def x(self):
        return (self.x0 + self.x1) / 2

    @property
    def y(self):
        return (self.y0 + self.y1) / 2


def _walk(item):
    yield item
    if hasattr(item, "__iter__"):
        for child in item:
            yield from _walk(child)


def _words(line):
    from pdfminer.layout import LTChar

    chars = []
    for item in [*line, None]:
        if isinstance(item, LTChar) and not item.get_text().isspace():
            chars.append(item)
        elif chars:
            yield Word(
                "".join(c.get_text() for c in chars),
                min(c.x0 for c in chars),
                min(c.y0 for c in chars),
                max(c.x1 for c in chars),
                max(c.y1 for c in chars),
            )
            chars.clear()


def _layout(content: bytes, page_number: int):
    from pdfminer.converter import PDFPageAggregator
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage

    class TextImages(PDFPageAggregator):
        # Provider booklets can contain hundreds of thousands of paths in an
        # unrelated street map. They add no information to a raster-icon grid.
        def paint_path(self, *args, **kwargs):
            pass

    manager = PDFResourceManager()
    device = TextImages(manager, laparams=LAParams(all_texts=True))
    interpreter = PDFPageInterpreter(manager, device)
    try:
        for index, page in enumerate(PDFPage.get_pages(BytesIO(content))):
            if index == page_number:
                interpreter.process_page(page)
                return device.get_result()
        raise ValueError("Missing calendar page")
    finally:
        device.close()


def _thumbnail(image):
    from PIL import Image

    rgba = image.convert("RGBA")
    white = Image.new("RGBA", rgba.size, "white")
    white.alpha_composite(rgba)
    rgb = white.convert("RGB").resize((16, 16))
    return list(rgb.getdata()), image.width / image.height


def _distance(first, second):
    pixels_a, aspect_a = first
    pixels_b, aspect_b = second
    error = sum(
        abs(a - b)
        for rgb_a, rgb_b in zip(pixels_a, pixels_b, strict=True)
        for a, b in zip(rgb_a, rgb_b, strict=True)
    ) / (256 * 3 * 255)
    return error + abs(aspect_a - aspect_b) * 0.1


def match_image(image, templates, *, threshold=0.12):
    distances = sorted(
        (_distance(image, ref), label) for label, ref in templates.items()
    )
    if (
        len(distances) < 2
        or distances[0][0] > threshold
        or distances[1][0] - distances[0][0] < 0.02
    ):
        raise ValueError("Unrecognised or ambiguous bin picture")
    return distances[0][1]


class IconMonthGridParser(Parser):
    """A complete grid page with printed month/year headings and a raster legend.

    ``legend`` maps a distinct word in each legend caption to the output label.
    ``legend_band`` is its vertical band as fractions of page height. Calendar
    day numerals are restricted by font height to exclude prose in blank cells.
    Every month's days and their printed weekday columns are checked. All
    symbols inside a dated cell must match a legend item.
    """

    def __init__(
        self,
        *,
        page: int,
        legend: dict[str, str],
        legend_band=(0.05, 0.14),
        day_font_size=(8.3, 8.6),
        min_months=12,
        threshold=0.12,
    ):
        self.page = page
        self.legend = dict(legend)
        self.legend_band = legend_band
        self.day_font_size = day_font_size
        self.min_months = min_months
        self.threshold = threshold
        self._cached: tuple[bytes, tuple[tuple[datetime.date, str], ...]] | None = None

    def __call__(self, response, source=None):
        cached = self._cached
        if cached is not None and cached[0] == response.content:
            return list(cached[1])
        records = self._parse(response.content)
        self._cached = (response.content, records)
        return list(records)

    def _parse(self, content):
        from pdfminer.layout import LTImage, LTTextLine
        from pypdf import PdfReader

        layout = _layout(content, self.page)
        objects = list(_walk(layout))
        lines = [o for o in objects if isinstance(o, LTTextLine)]
        words = [w for line in lines for w in _words(line)]
        images = [o for o in objects if isinstance(o, LTImage)]
        page = PdfReader(BytesIO(content)).pages[self.page]
        thumbnails = {}

        def thumbnail(image):
            key = image.stream.objid
            if key not in thumbnails:
                thumbnails[key] = _thumbnail(page.images["/" + image.name].image)
            return thumbnails[key]

        templates = {}
        for token, label in self.legend.items():
            captions = [
                w
                for w in words
                if w.text == token
                and layout.height * self.legend_band[0]
                < w.y
                < layout.height * self.legend_band[1]
            ]
            candidates = [
                (abs(w.x - (im.x0 + im.x1) / 2) + abs(w.y - (im.y0 + im.y1) / 2), im)
                for w in captions
                for im in images
                if 0 < w.x - (im.x0 + im.x1) / 2 < 65
                and abs(w.y - (im.y0 + im.y1) / 2) < 40
                and im.width > 30
                and im.height > 30
            ]
            if not candidates:
                raise ValueError(f"Missing raster legend item: {token}")
            templates[label] = thumbnail(min(candidates, key=lambda c: c[0])[1])

        headings = {}
        for line in lines:
            text = " ".join(line.get_text().split())
            match = re.fullmatch(r"([A-Za-z]+) (20\d{2})", text)
            month = recurrence.month(match[1]) if match else None
            if month is not None and match is not None:
                headings[(int(match[2]), month)] = Word(
                    text, line.x0, line.y0, line.x1, line.y1
                )
        if len(headings) < self.min_months:
            raise ValueError("Incomplete printed month grid")
        ordered = sorted(headings)
        if any(b[0] * 12 + b[1] != a[0] * 12 + a[1] + 1 for a, b in pairwise(ordered)):
            raise ValueError("Printed calendar months are not consecutive")
        results = set()
        for (year, month), heading in headings.items():
            peers = [h for h in headings.values() if abs(h.y - heading.y) < 3]
            pitch_x = median(b - a for a, b in pairwise(sorted(h.x for h in peers)))
            left, right = heading.x - pitch_x / 2, heading.x + pitch_x / 2
            below = [
                h
                for h in headings.values()
                if h.y < heading.y - 3 and abs(h.x - heading.x) < pitch_x / 2
            ]
            bottom = max((h.y for h in below), default=0) + 10
            numbers = [
                w
                for w in words
                if w.text.isdigit()
                and 1 <= int(w.text) <= 31
                and left < w.x < right
                and bottom < w.y < heading.y - 15
                and self.day_font_size[0] <= w.y1 - w.y0 <= self.day_font_size[1]
            ]
            # A PDF can draw an identical grid twice (overprinting). Retain one
            # copy, while conflicting day numbers at one position still fail.
            numbers = list(
                {(w.text, round(w.x, 2), round(w.y, 2)): w for w in numbers}.values()
            )
            if len(numbers) != calendar.monthrange(year, month)[1] or {
                int(w.text) for w in numbers
            } != set(range(1, len(numbers) + 1)):
                raise ValueError(f"Incomplete printed days in {year}-{month}")
            columns = [
                [
                    w
                    for w in numbers
                    if (datetime.date(year, month, int(w.text)).weekday() + 1) % 7
                    == col
                ]
                for col in range(7)
            ]
            starts = [min(w.x0 for w in col) - 2 for col in columns]
            if starts != sorted(starts):
                raise ValueError("Printed days disagree with weekday columns")
            edges = [*starts, starts[-1] + starts[1] - starts[0]]
            levels = sorted({round(w.y, 1) for w in numbers}, reverse=True)
            pitch_y = median(a - b for a, b in pairwise(levels))
            date_cells = {}
            for w in numbers:
                date = datetime.date(year, month, int(w.text))
                col = (date.weekday() + 1) % 7
                if not edges[col] <= w.x < edges[col + 1]:
                    raise ValueError("A printed day is outside its weekday cell")
                for image in images:
                    x, y = (image.x0 + image.x1) / 2, (image.y0 + image.y1) / 2
                    if (
                        edges[col] <= x < edges[col + 1]
                        and w.y - pitch_y + 5 < y <= w.y + 5
                    ):
                        if not (10 < image.width < 30 and 10 < image.height < 35):
                            raise ValueError(
                                "Unexpected image size inside the calendar grid"
                            )
                        key = image.stream.objid
                        if key not in date_cells:
                            date_cells[key] = match_image(
                                thumbnail(image), templates, threshold=self.threshold
                            )
                        results.add((date, date_cells[key]))
        if not results:
            raise ValueError("No dated bin icons found")
        return tuple(sorted(results))


class CollectionWeekday:
    """Match ordered, printed collection days to a household's usual weekdays.

    Holiday weeks can have their last collection on Saturday. The printed icon
    dates are retained; no dates are generated from a weekday rule.
    """

    def __init__(self, weekdays=(2, 3, 4), day_param="day"):
        self.weekdays = tuple(weekdays)
        self.day_param = day_param

    def __call__(self, records, source):
        weekday = recurrence.weekday(source.params[self.day_param])
        if weekday not in self.weekdays:
            raise SourceArgumentNotFoundWithSuggestions(
                self.day_param,
                source.params[self.day_param],
                [calendar.day_name[day] for day in self.weekdays],
            )
        by_date = defaultdict(set)
        for day, label in records:
            by_date[day].add(label)
        first, last = min(by_date), max(by_date)
        start = first.replace(day=1)
        if not start <= datetime.date.today() <= last:
            raise ValueError("The published calendar does not cover today")
        weeks = defaultdict(list)
        for day in sorted(by_date):
            weeks[day - datetime.timedelta(days=day.weekday())].append(day)
        ordered_weeks = sorted(weeks)
        if any((b - a).days != 7 for a, b in pairwise(ordered_weeks)):
            raise ValueError("A printed collection week is missing")
        for monday, dates in sorted(weeks.items()):
            nominal = [monday + datetime.timedelta(days=i) for i in self.weekdays]
            nominal = [day for day in nominal if start <= day <= last]
            if len(nominal) != len(dates):
                raise ValueError("Incomplete printed collection week")
            for regular, actual in zip(nominal, dates, strict=True):
                if regular.weekday() == weekday:
                    for label in sorted(by_date[actual]):
                        yield {
                            "date": actual,
                            "type": label,
                            "description": "Natural Christmas trees only"
                            if label == "Christmas trees"
                            else None,
                        }
