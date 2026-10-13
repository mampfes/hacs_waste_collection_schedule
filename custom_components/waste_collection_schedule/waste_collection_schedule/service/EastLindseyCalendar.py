"""Read the dated, colour-highlighted East Lindsey garden-waste calendar.

The lookup's ``greenfirst`` is a season anchor, not the next collection.
The linked PDF prints each month and year, including the reduced winter
service. Read its highlighted date cells instead of projecting a recurrence.
"""

import calendar
import re
from datetime import date
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser, PdfWordLayoutParser
from waste_collection_schedule.service.GossForm import form_data

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_MONTHS = {name: month for month, name in enumerate(calendar.month_name) if name}
_MONTH_HEADER = re.compile(r"([A-Za-z]+) (20\d{2})")


_LOOKUP_FIELDS = (
    ("wastenextref", "Refuse"),
    ("wastenextrec", "Recycling"),
    ("wastenextpur", "Purple Bin"),
)
_CALENDAR_URL = "https://www.e-lindsey.gov.uk/media/{id}/file/PDF/{day}{week}.pdf"


def _lookup_result(response: "Response") -> dict[str, Any] | None:
    """The property's row of the lookup reply, or ``None`` when it has none."""
    results = form_data(response).get("RESULTS_1", {}).get("FIELD12", {}).get("result")
    return results[0] if results else None


def garden_calendar_urls(source: "BaseSource", response: "Response") -> list[str]:
    """The property's garden-waste calendar PDF, or none without a subscription.

    ``greenfirst`` is the start of the season, not an upcoming collection; the
    dated schedule is the PDF named by the lookup's id, weekday and A/B week.
    """
    result = _lookup_result(response) or {}
    pdf_id = result.get("greenpdfid")
    if pdf_id in (None, "", "null"):
        return []
    day = str(result.get("greenday", "")).strip()
    week = str(result.get("greenweek", "")).strip()
    response_shape.expect(
        str(pdf_id).isdigit()
        and day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
        and week in ("A", "B"),
        source_name=response_shape.source_name(source),
        detail="garden calendar lookup has invalid id/day/week fields",
    )
    return [_CALENDAR_URL.format(id=pdf_id, day=day, week=week)]


class LookupParser(Parser[list[tuple[str, str]]]):
    """``(date text, label)`` for each next collection the lookup reply names."""

    def __call__(
        self, response: "Response", source: "BaseSource | None" = None
    ) -> list[tuple[str, str]]:
        result = _lookup_result(response)
        if result is None:
            raise SourceArgumentNotFound(
                "uprn", source.params.get("uprn") if source else None
            )
        return [
            (str(result[field]), label)
            for field, label in _LOOKUP_FIELDS
            if result.get(field)
        ]


class GardenCalendarParser(Parser[Any]):
    """Read only cells highlighted in the colour of the Green Waste legend.

    Returns the sorted dates, or ``(date, label)`` rows when ``label`` is given.
    """

    def __init__(self, label: str | None = None):
        self.label = label

    def __call__(
        self, response: "Response", source: "BaseSource | None" = None
    ) -> list[Any]:
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
        days = sorted(dates)
        return days if self.label is None else [(day, self.label) for day in days]
