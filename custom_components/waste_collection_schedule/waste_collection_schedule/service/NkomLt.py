"""PDF schedule parser for Nemėžio komunalininkas."""

import re
import unicodedata
from collections import defaultdict
from datetime import date
from io import BytesIO
from typing import Any
from urllib.parse import unquote, urlparse

from pypdf import PdfReader

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.response_shape import ResponseShapeError

_SOURCE_NAME = "Nemėžio komunalininkas"
_MONTHS = {
    "sausis": 1,
    "vasaris": 2,
    "kovas": 3,
    "balandis": 4,
    "geguze": 5,
    "birzelis": 6,
    "liepa": 7,
    "rugpjutis": 8,
    "rugsejis": 9,
    "spalis": 10,
    "lapkritis": 11,
    "gruodis": 12,
}
_ROUTE_RE = re.compile(r"\b[A-Z]{3}\s*\d{3}(?:\s*\(\d+\))?\b")
_DATE_LIST_RE = re.compile(r"\d{1,2}(?:\s*,\s*\d{1,2})*")
_MAX_PDF_BYTES = 5 * 1024 * 1024


def _fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value).casefold()
        if not unicodedata.combining(character)
    )


def _schedule_kind(url: str) -> str | None:
    filename = _fold(unquote(urlparse(url).path))
    if not filename.endswith(".pdf") or "grafikas" not in filename:
        return None
    if "pakuociu" in filename:
        return "packaging"
    if "misriu" in filename:
        return "mixed"
    return None


def _extract_spans(page) -> list[tuple[float, float, str]]:
    height = float(page.mediabox.height)
    spans: list[tuple[float, float, str]] = []

    def visitor(text, ctm, text_matrix, _font_dict, font_size):
        a, b, c, d, e, f = ctm
        x = a * text_matrix[4] + c * text_matrix[5] + e
        y = height - (b * text_matrix[4] + d * text_matrix[5] + f)
        for line_number, line in enumerate(text.splitlines()):
            if line.strip():
                spans.append((x, y + line_number * float(font_size), line.strip()))

    page.extract_text(visitor_text=visitor)
    return spans


def _header_layout(
    spans: list[tuple[float, float, str]],
) -> tuple[list[tuple[int, float]], float, float, float] | None:
    headers: dict[str, float] = {}
    months: list[tuple[int, float]] = []
    for x, y, text in spans:
        if y > 190:
            continue
        normalized = _fold(text.strip(" :"))
        if normalized == "seniunija":
            headers["district"] = x
        elif normalized == "vietove":
            headers["location"] = x
        elif normalized.startswith("sav."):
            headers["weekday"] = x
        elif normalized in _MONTHS:
            months.append((_MONTHS[normalized], x))

    months.sort(key=lambda month: month[1])
    if (
        "district" not in headers
        or "location" not in headers
        or len(months) not in (3, 6)
    ):
        return None

    first_month_x = months[0][1]
    locality_start = 120.0 if len(months) == 3 else 100.0
    locality_end = headers.get("weekday", first_month_x) - 15.0
    return months, headers["district"], locality_start, locality_end


def _group_lines(spans: list[tuple[float, float, str]]) -> list[tuple[float, str]]:
    lines: list[list[tuple[float, float, str]]] = []
    for span in sorted(spans, key=lambda item: (item[1], item[0])):
        if not lines or abs(span[1] - lines[-1][0][1]) > 2.0:
            lines.append([span])
        else:
            lines[-1].append(span)
    return [
        (
            sum(span[1] for span in line) / len(line),
            " ".join(span[2] for span in sorted(line, key=lambda item: item[0])),
        )
        for line in lines
    ]


def _parse_pdf(content: bytes, kind: str, location: str) -> list[dict[str, Any]]:
    if len(content) > _MAX_PDF_BYTES:
        raise ValueError(f"NKOM {kind} schedule PDF exceeds {_MAX_PDF_BYTES} bytes")

    reader = PdfReader(BytesIO(content))
    if not reader.pages:
        raise ValueError(f"NKOM {kind} schedule PDF has no pages")

    year_match = re.search(r"\b(20\d{2})\b", reader.pages[0].extract_text() or "")
    if year_match is None:
        raise ResponseShapeError(
            _SOURCE_NAME, f"Could not determine the year in the NKOM {kind} schedule"
        )
    year = int(year_match.group(1))
    folded_location = _fold(location)
    entries: list[dict[str, Any]] = []
    header_layout = None
    found_rows = False

    for page in reader.pages:
        spans = _extract_spans(page)
        page_layout = _header_layout(spans)
        if page_layout is not None:
            header_layout = page_layout
        if header_layout is None:
            continue
        month_columns, district_x, locality_start, locality_end = header_layout
        route_lines = [
            (y, text) for y, text in _group_lines(spans) if _ROUTE_RE.search(text)
        ]
        if not route_lines:
            continue
        found_rows = True

        page_height = float(page.mediabox.height)
        for index, (row_y, _row_text) in enumerate(route_lines):
            previous_y = route_lines[index - 1][0] if index else 0.0
            next_y = (
                route_lines[index + 1][0]
                if index + 1 < len(route_lines)
                else page_height
            )
            location_top = (previous_y + row_y) / 2
            location_bottom = (row_y + next_y) / 2
            if index == 0:
                location_top = max(location_top, row_y - 25.0)

            row_spans = [span for span in spans if abs(span[1] - row_y) <= 2.0]
            district = " ".join(
                span[2]
                for span in sorted(
                    (
                        span
                        for span in row_spans
                        if span[0] < locality_start and abs(span[0] - district_x) < 100
                    ),
                    key=lambda item: item[0],
                )
            )
            row_location = " ".join(
                span[2]
                for span in sorted(
                    (
                        span
                        for span in spans
                        if locality_start <= span[0] < locality_end
                        and location_top <= span[1] < location_bottom
                    ),
                    key=lambda item: (item[1], item[0]),
                )
            )
            if folded_location not in _fold(f"{district} {row_location}"):
                continue

            date_cells: dict[int, list[str]] = defaultdict(list)
            for span in row_spans:
                if not _DATE_LIST_RE.fullmatch(span[2]):
                    continue
                column_index = min(
                    range(len(month_columns)),
                    key=lambda month_index: abs(
                        span[0] - month_columns[month_index][1]
                    ),
                )
                if abs(span[0] - month_columns[column_index][1]) < 35:
                    date_cells[column_index].append(span[2])

            for column_index, (month, _x) in enumerate(month_columns):
                kind_label = (
                    "mixed"
                    if kind == "mixed"
                    else "packaging"
                    if column_index < 3
                    else "glass"
                )
                for value in date_cells.get(column_index, []):
                    for day_text in re.findall(r"\d{1,2}", value):
                        day = int(day_text)
                        try:
                            event_date = date(year, month, day)
                        except ValueError as exc:
                            raise ResponseShapeError(
                                _SOURCE_NAME,
                                f"Invalid date in the NKOM {kind} schedule: "
                                f"{year}-{month:02d}-{day:02d}",
                            ) from exc
                        entries.append({"date": event_date, "type": kind_label})

    if header_layout is None:
        raise ResponseShapeError(
            _SOURCE_NAME, f"Could not find the table in the NKOM {kind} PDF"
        )
    if not found_rows:
        raise ResponseShapeError(
            _SOURCE_NAME, f"Could not find schedule rows in the NKOM {kind} PDF"
        )
    return entries


class NkomParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("NKOM parser requires a source")
        kind = _schedule_kind(response.url)
        if kind is None:
            raise ResponseShapeError(
                _SOURCE_NAME, f"Unexpected NKOM schedule URL: {response.url}"
            )
        return _parse_pdf(response.content, kind, source.params["location"])
