"""Read the council's printed month rows, including dated holiday exceptions."""

import calendar
import datetime
import re
from io import BytesIO

from waste_collection_schedule import recurrence
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.service.PdfVectorDigits import TAHOMA_BOLD, VectorDigits

_BLUE = (0.098, 0.4627, 0.8235)
_BROWN = (0.4745, 0.3333, 0.2824)
_WHITE = (1.0, 1.0, 1.0)


def _walk(item):
    yield item
    if hasattr(item, "__iter__"):
        for child in item:
            yield from _walk(child)


def _color(actual, expected):
    return (
        isinstance(actual, (list, tuple))
        and len(actual) == len(expected)
        and all(abs(a - b) < 0.01 for a, b in zip(actual, expected, strict=True))
    )


class CalendarParser(Parser):
    """Read the 13 dated rows (April to April), without projecting a bin cycle."""

    def __call__(self, response, source=None):
        from pdfminer.high_level import extract_pages, extract_text
        from pdfminer.layout import LTCurve

        text = extract_text(BytesIO(response.content))
        match = re.search(r"Calendar\s+(20\d{2})\s*-\s*(20\d{2})", text)
        if match is None or int(match[2]) != int(match[1]) + 1:
            raise ValueError("Missing printed calendar year range")
        year = int(match[1])
        if (
            not datetime.date(year, 4, 1)
            <= datetime.date.today()
            <= datetime.date(year + 1, 4, 30)
        ):
            raise ValueError("The council's published calendar has expired")
        pages = list(extract_pages(BytesIO(response.content)))
        if len(pages) != 1:
            raise ValueError("Expected a single council calendar sheet")
        curves = [x for x in _walk(pages[0]) if isinstance(x, LTCurve) and x.fill]
        cells = [
            x
            for x in curves
            if 12 < x.height < 18
            and 20 < x.width < 60
            and (
                _color(x.non_stroking_color, _BLUE)
                or _color(x.non_stroking_color, _BROWN)
            )
        ]
        rows = []
        for cell in sorted(cells, key=lambda c: -c.y0):
            if not rows or abs(rows[-1][0].y0 - cell.y0) > 1:
                rows.append([cell])
            else:
                rows[-1].append(cell)
        if len(rows) != 13:
            raise ValueError("Expected 13 printed monthly collection rows")
        decoder = VectorDigits(TAHOMA_BOLD)
        results = set()
        for index, row in enumerate(rows):
            absolute_month = 3 + index
            month_year, month = year + absolute_month // 12, absolute_month % 12 + 1
            days = []
            if not 3 <= len(row) <= 6:
                raise ValueError("Incomplete monthly collection row")
            for cell in sorted(row, key=lambda c: c.x0):
                brown = _color(cell.non_stroking_color, _BROWN)
                left = cell.x0 - cell.width if brown else cell.x0
                # A brown event is drawn as adjacent black and brown halves.
                if brown and not any(
                    _color(other.non_stroking_color, (0, 0, 0))
                    and abs(other.x1 - cell.x0) < 0.1
                    and abs(other.y0 - cell.y0) < 0.1
                    and abs(other.width - cell.width) < 0.1
                    for other in curves
                ):
                    raise ValueError("Missing black half of the combined bin cell")
                digits = [
                    x
                    for x in curves
                    if _color(x.non_stroking_color, _WHITE)
                    and 8 < x.height < 13
                    and 2 < x.width < 12
                    and left <= (x.x0 + x.x1) / 2 <= cell.x1
                    and cell.y0 <= (x.y0 + x.y1) / 2 <= cell.y1
                ]
                day = decoder.read(digits)
                if not 1 <= day <= calendar.monthrange(month_year, month)[1]:
                    raise ValueError("Invalid printed calendar day")
                days.append(day)
                date = datetime.date(month_year, month, day)
                labels = ("Black bin", "Brown bin") if brown else ("Blue bin",)
                results.update((date, label) for label in labels)
            if days != sorted(set(days)):
                raise ValueError(
                    "Printed collection days are duplicated or out of order"
                )
        # Month captions are outlined too. The route code independently checks
        # their April-to-April ordering: a shifted month/year would put most
        # dates on another weekday. A few explicitly printed holiday exceptions
        # remain valid, including the Friday shown in the Wednesday calendar.
        code = re.search(
            r"/(MON|TUE|WED|THU|FRI)-Z\d+\.pdf", str(getattr(response, "url", "")), re.I
        )
        if code:
            weekday = recurrence.weekday(code[1])
            dates = {day for day, _ in results}
            if sum(day.weekday() != weekday for day in dates) > max(
                2, len(dates) // 10
            ):
                raise ValueError(
                    "Calendar months disagree with the printed route weekday"
                )
        return sorted(results)
