"""Read the dated, colour-highlighted East Lindsey garden-waste calendar.

The lookup's ``greenfirst`` is a season anchor, not the next collection.
The linked PDF prints each month and year, including the reduced winter
service. Read its highlighted date cells instead of projecting a recurrence.
"""

import calendar
import re
from datetime import date
from typing import TYPE_CHECKING

from waste_collection_schedule import response_shape
from waste_collection_schedule.parsers import Parser, PdfWordLayoutParser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_MONTHS = {name: month for month, name in enumerate(calendar.month_name) if name}
_MONTH_HEADER = re.compile(r"([A-Za-z]+) (20\d{2})")


class GardenCalendarParser(Parser[list[date]]):
    """Read only cells highlighted in the colour of the Green Waste legend."""

    def __call__(
        self, response: "Response", source: "BaseSource | None" = None
    ) -> list[date]:
        name = response_shape.source_name(source) if source else "e_lindsey_gov_uk"
        # The mini-calendars are scaled PDF Form XObjects. Without all_texts,
        # pdfminer leaves their glyphs ungrouped and no day words are returned.
        layout = PdfWordLayoutParser(
            include_form_text=True, min_words=100, min_vectors=30
        )(response, source)[0]
        headers = []
        for line in layout.lines:
            match = _MONTH_HEADER.fullmatch(line.text)
            if match and match[1] in _MONTHS:
                headers.append((line, _MONTHS[match[1]], int(match[2])))
        response_shape.expect(
            len(headers) >= 12,
            source_name=name,
            detail="garden calendar has too few dated month headers",
        )

        legends = [
            line for line in layout.lines if line.text.casefold() == "green waste"
        ]
        legend_boxes = [
            vector
            for vector in layout.vectors
            if vector.fill_color is not None
            and any(
                vector.page == line.page
                and vector.y0 <= line.y <= vector.y1
                and 0 < line.x - vector.x1 < 80
                for line in legends
            )
        ]
        response_shape.expect(
            bool(legend_boxes),
            source_name=name,
            detail="garden calendar has no Green Waste colour legend",
        )
        legend = max(legend_boxes, key=lambda vector: vector.x1)
        assert legend.fill_color is not None
        numbers = [word for word in layout.words if word.text.isdigit()]
        dates = set()
        for vector in layout.vectors:
            fill = vector.fill_color
            if vector == legend or fill is None or len(fill) != len(legend.fill_color):
                continue
            if any(
                abs(a - b) > 0.005 for a, b in zip(fill, legend.fill_color, strict=True)
            ):
                continue
            cells = [
                word
                for word in numbers
                if word.page == vector.page
                and vector.x0 <= word.x <= vector.x1
                and vector.y0 <= word.y <= vector.y1
            ]
            response_shape.expect(
                len(cells) == 1,
                source_name=name,
                detail="garden calendar highlight does not contain one date",
            )
            cell = cells[0]
            above = [
                header
                for header in headers
                if header[0].page == cell.page and header[0].y > cell.y
            ]
            response_shape.expect(
                bool(above),
                source_name=name,
                detail="garden calendar date has no month header",
            )
            band_y = min(header[0].y for header in above)
            _, month, year = min(
                (header for header in above if abs(header[0].y - band_y) < 2),
                key=lambda header: abs(header[0].x - cell.x),
            )
            try:
                collection_date = date(year, month, int(cell.text))
            except ValueError:
                collection_date = None
            response_shape.expect(
                collection_date is not None,
                source_name=name,
                detail="garden calendar contains an invalid highlighted date",
            )
            assert collection_date is not None
            dates.add(collection_date)
        response_shape.expect(
            bool(dates),
            source_name=name,
            detail="garden calendar contains no highlighted collection dates",
        )
        return sorted(dates)
