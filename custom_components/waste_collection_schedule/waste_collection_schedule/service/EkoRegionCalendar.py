"""Read EKO-REGION's annual outlined month tables, including ash annotations.

The PDF has no text layer for its dates. Path topology and geometric moments
identify its printed glyphs; table ruling supplies the months and columns.
Unknown glyphs, incomplete tables and stale years fail without guessing dates.
"""

import datetime
import re
from io import BytesIO

from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.service.PdfRuledTable import collapse_edges
from waste_collection_schedule.service.PdfVectorDigits import VectorDigits

# Aggregate signatures of the public calendar's outlined typeface. These are
# font measurements, not collection dates or weekday rules.
_GLYPHS = {
    "0": ("mcccccccccccccccc", (0.82608, 0.52929, 0.50003, 0.38124, 0.3495)),
    "1": (
        "mcccclcccccccclllcccccccclccccccccllcccc",
        (0.71059, 0.41483, 0.45232, 0.39365, 0.42239),
    ),
    "2": (
        "mcccclcccccccclccccccccccccccccccccccccccccccccllcccc",
        (0.75875, 0.44988, 0.50728, 0.38116, 0.37794),
    ),
    "3": (
        "mcccccccccccccccccccccccccclcccccccclcccccccccccccccccccccccccccccccclcccc",
        (0.74839, 0.41045, 0.51223, 0.31925, 0.31398),
    ),
    "4": (
        "mccllccccccccllcccccccclccccccccllcc",
        (0.87628, 0.57425, 0.39338, 0.34615, 0.36406),
    ),
    "5": (
        "mcccccccccccccccccccccccccccccccclcclccccccllcccccc",
        (0.76475, 0.43825, 0.41723, 0.35308, 0.33608),
    ),
    "6": (
        "mcccccccccccccccccccccccccccccccccccccccccccc",
        (0.78494, 0.5828, 0.63903, 0.33757, 0.31769),
    ),
    "7": ("mcccclccccccccllcccccclcccc", (0.79786, 0.49776, 0.63234, 0.40729, 0.43921)),
    "8": (
        "mcccccccccccccccccccccccccccccccc",
        (0.8046, 0.51546, 0.49945, 0.367, 0.31129),
    ),
    "9": (
        "mcccccccccccccccccccccccccccccccccccccccc",
        (0.78638, 0.4353, 0.37145, 0.35371, 0.32238),
    ),
    ",": ("mcccclccccccccllcccccccc", (0.78542, 0.54348, 0.52027, 0.3496, 0.40933)),
    "(": (
        "mcccccccccccccccccccccccccccc",
        (0.25491, 0.63351, 0.51668, 0.3151, 0.42082),
    ),
    ")": ("mcccccccccccccccccccccccccc", (0.25418, 0.37041, 0.48181, 0.31792, 0.4196)),
    "p": (
        "mcccccccclcccccccclcccccccclcccccccc",
        (0.763, 0.34786, 0.56135, 0.33178, 0.40527),
    ),
    "o": ("mcccccccccccccccc", (1.11843, 0.52904, 0.50064, 0.37349, 0.34814)),
    "i": ("mcccccccclcccccccc", (0.21076, 0.49776, 0.49963, 0.39347, 0.48653)),
    "ł": (
        "mccccllccccccccllccccccllccccccccllcc",
        (0.3974, 0.51283, 0.54924, 0.32272, 0.3511),
    ),
    ".": ("mcccccccc", (1.26531, 0.55573, 0.49999, 0.38598, 0.35316)),
    "'": ("mcccccccclcccccccc", (1.312, 0.47319, 0.4961, 0.33891, 0.44993)),
}

_LABELS = (
    "Metale i tworzywa sztuczne",
    "Papier",
    "Szkło",
    "Bio",
    "Zmieszane odpady komunalne",
)
_COLORS = (
    (1.0, 0.9294, 0.0),
    (0.5137, 0.8157, 0.9569),
    (0.5294, 0.7451, 0.2706),
    (0.7059, 0.4627, 0.2824),
    (0.7725, 0.7765, 0.7765),
)


def _walk(item):
    yield item
    if hasattr(item, "__iter__"):
        for child in item:
            yield from _walk(child)


def _color(actual, expected):
    return (
        isinstance(actual, (tuple, list))
        and len(actual) == len(expected)
        and all(abs(a - b) < 0.02 for a, b in zip(actual, expected, strict=True))
    )


def _cell_text(shapes, decoder):
    # A compound outline can expose its inner holes as separate curves. Keep
    # only the outer glyph, never recognise the hole as another character.
    outer = [
        c
        for c in shapes
        if not any(
            other is not c
            and other.x0 <= c.x0 + 0.01
            and other.x1 >= c.x1 - 0.01
            and other.y0 <= c.y0 + 0.01
            and other.y1 >= c.y1 - 0.01
            and other.width * other.height > c.width * c.height * 1.1
            for other in shapes
        )
    ]
    parsed = [(shape, decoder.glyph(shape)) for shape in outer]
    levels = []
    for shape, text in sorted(parsed, key=lambda item: -item[0].y0):
        if text.isdigit():
            y = (shape.y0 + shape.y1) / 2
            if not levels or abs(levels[-1] - y) > 2:
                levels.append(y)
    if parsed and not levels:
        raise ValueError("Calendar cell contains no readable day numbers")
    groups = [[] for _ in levels]
    for shape, text in parsed:
        index = min(
            range(len(levels)), key=lambda i: abs(levels[i] - (shape.y0 + shape.y1) / 2)
        )
        if abs(levels[index] - (shape.y0 + shape.y1) / 2) > 3.5:
            raise ValueError("Unaligned calendar annotation")
        groups[index].append((shape, text))
    for group in groups:
        # The dot over i and the accent over ó are separate outline paths.
        # Their shapes are validated too, then omitted from the normalised word.
        yield "".join(
            text
            for _, text in sorted(group, key=lambda item: item[0].x0)
            if text not in (".", "'")
        )


class CalendarParser(Parser):
    """The one-page January-December residential schedule, five waste columns."""

    def __call__(self, response, source=None):
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTCurve
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(response.content))
        if len(reader.pages) != 1:
            raise ValueError("Expected a single residential calendar page")
        text = reader.pages[0].extract_text()
        match = re.search(r"KALENDARZ\s+ODBIORU\s+ODPADÓW\s+(20\d{2})", text, re.I)
        if match is None:
            raise ValueError("No printed EKO-REGION calendar year")
        year = int(match[1])
        if year != datetime.date.today().year:
            raise ValueError("The provider has not published a current-year calendar")
        curves = [
            c
            for page in extract_pages(BytesIO(response.content))
            for c in _walk(page)
            if isinstance(c, LTCurve)
        ]
        rules = [
            c
            for c in curves
            if len(c.original_path) <= 6
            and not any(p[0] == "c" for p in c.original_path)
        ]
        xs = collapse_edges([c.x0 for c in rules if c.height > 5 and c.width < 3])
        ys = collapse_edges([c.y0 for c in rules if c.width > 200 and c.height < 3])[
            ::-1
        ]
        if len(xs) != 7 or len(ys) != 14:
            raise ValueError("Expected twelve month rows and five waste columns")
        for column, color in enumerate(_COLORS, 1):
            x = (xs[column] + xs[column + 1]) / 2
            y = (ys[0] + ys[1]) / 2
            if not any(
                c.fill
                and _color(c.non_stroking_color, color)
                and c.x0 <= x <= c.x1
                and c.y0 <= y <= c.y1
                for c in curves
            ):
                raise ValueError("The waste column headings have changed")
        decoder = VectorDigits(_GLYPHS)
        results = set()
        for month in range(1, 13):
            top, bottom = ys[month : month + 2]
            for column, label in enumerate(_LABELS, 1):
                left, right = xs[column : column + 2]
                shapes = [
                    c
                    for c in curves
                    if c.fill
                    and _color(c.non_stroking_color, (0, 0, 0))
                    and 0.05 < c.width < 5
                    and 0.05 < c.height < 6
                    and left < (c.x0 + c.x1) / 2 < right
                    and bottom < (c.y0 + c.y1) / 2 < top
                ]
                lines = list(_cell_text(shapes, decoder))
                if column in (1, 5) and not lines:
                    raise ValueError("A monthly residual or recycling entry is missing")
                for line in lines:
                    match = re.fullmatch(r"(\d{1,2}(?:,\d{1,2})*)(\(popioł\))?", line)
                    if match is None or (match[2] and column != 4):
                        raise ValueError(f"Unexpected calendar cell text: {line}")
                    waste_type = "Popiół" if match[2] else label
                    days = [int(d) for d in match[1].split(",")]
                    if days != sorted(set(days)):
                        raise ValueError("Duplicated or unsorted collection days")
                    results.update(
                        (datetime.date(year, month, day), waste_type) for day in days
                    )
        return sorted(results)
