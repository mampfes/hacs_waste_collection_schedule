import logging
import re
from datetime import date
from io import BytesIO
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTChar,
    LTContainer,
    LTCurve,
    LTFigure,
    LTPage,
    LTTextBoxHorizontal,
    LTTextLineHorizontal,
)
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "ETRA S.p.A."
DESCRIPTION = "Waste collection schedule for San Martino di Lupari, Italy."
URL = "https://www.etraspa.it"
COUNTRY = "it"
SOURCE_CODEOWNERS = ["@jan-tdy"]

TEST_CASES = {
    "San Martino di Lupari, zone B": {"zone": "B"},
    "San Martino di Lupari, zone A": {"zone": "A"},
}

PARAM_DESCRIPTIONS = {
    "en": {"zone": "The collection zone shown on the ETRA calendar (A or B)."},
    "it": {"zone": "La zona di raccolta indicata nel calendario ETRA (A o B)."},
}
PARAM_TRANSLATIONS = {
    "en": {"zone": "Collection zone"},
    "it": {"zone": "Zona di raccolta"},
}

ICON_MAP = {
    "Secco residuo": Icons.GENERAL_WASTE,
    "Plastica e metalli": Icons.RECYCLING,
    "Carta e cartone": Icons.PAPER,
    "Vetro": Icons.GLASS,
    "Verde e ramaglie": Icons.GARDEN,
    "Umido organico": Icons.ORGANIC,
}

_LOGGER = logging.getLogger(__name__)

_DOCUMENT_URL = (
    "https://www.comune.sanmartinodilupari.pd.it/"
    "documento_pubblico/calendario-etra-{year}/"
)
_HEADERS = {"User-Agent": "waste-collection-schedule/etraspa_it"}
_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}
_MONTH_RE = re.compile(r"^(" + "|".join(_MONTHS) + r")\b", re.IGNORECASE)
_DAY_RE = re.compile(r"^(\d{1,2})\s*[A-Z]$")
_YEAR_RE = re.compile(r"CALENDARIO\s+(20\d{2})", re.IGNORECASE)

# RGB fill colours used by the collection symbols in ETRA's InDesign PDF.
_COLOUR_MAP = {
    (0.614, 0.644, 0.681): "Secco residuo",
    (0.993, 0.765, 0.0): "Plastica e metalli",
    (0.0, 0.336, 0.617): "Carta e cartone",
    (0.23, 0.491, 0.202): "Vetro",
    (0.848, 0.736, 0.581): "Verde e ramaglie",
    (0.441, 0.305, 0.26): "Umido organico",
}
_COLOUR_TOLERANCE = 0.01
_MAX_ZONE_DISTANCE = 32
_MAX_DAY_DISTANCE = 7


def _iter_elements(container: LTContainer):
    for element in container:
        yield element
        if isinstance(element, LTContainer):
            yield from _iter_elements(element)


def _waste_type(colour) -> str | None:
    if not isinstance(colour, (list, tuple)) or len(colour) != 3:
        return None

    for expected, waste_type in _COLOUR_MAP.items():
        if all(
            abs(float(colour[index]) - expected[index]) <= _COLOUR_TOLERANCE
            for index in range(3)
        ):
            return waste_type
    return None


def _zone_centres(page: LTPage) -> list[tuple[float, float]]:
    """Return the horizontal centres of zone A and B for each month column."""
    columns: list[tuple[float, float]] = []

    for figure in page:
        if not isinstance(figure, LTFigure):
            continue

        chars = sorted(
            (
                element
                for element in _iter_elements(figure)
                if isinstance(element, LTChar) and element.get_text().strip()
            ),
            key=lambda element: element.x0,
        )
        if "".join(char.get_text() for char in chars).upper() != "ZONAAZONAB":
            continue

        zone_a = chars[:5]
        zone_b = chars[5:]
        columns.append(
            (
                (zone_a[0].x0 + zone_a[-1].x1) / 2,
                (zone_b[0].x0 + zone_b[-1].x1) / 2,
            )
        )

    return sorted(columns)


def _calendar_columns(
    page: LTPage, base_year: int
) -> list[tuple[int, int, list[tuple[int, float]], tuple[float, float]]]:
    headings: list[tuple[float, int]] = []
    date_columns: list[tuple[float, list[tuple[int, float]]]] = []

    for element in page:
        if not isinstance(element, LTTextBoxHorizontal):
            continue

        text = " ".join(element.get_text().split())
        if month_match := _MONTH_RE.match(text):
            headings.append((element.x0, _MONTHS[month_match.group(1).casefold()]))

        days: list[tuple[int, float]] = []
        for line in element:
            if not isinstance(line, LTTextLineHorizontal):
                continue
            if day_match := _DAY_RE.fullmatch(" ".join(line.get_text().split())):
                days.append((int(day_match.group(1)), (line.y0 + line.y1) / 2))
        if len(days) >= 28:
            date_columns.append((element.x0, days))

    headings.sort()
    date_columns.sort()
    zones = _zone_centres(page)
    if not headings or not (len(headings) == len(date_columns) == len(zones)):
        raise ValueError(
            "Could not identify all month, date, and zone columns in the ETRA PDF. "
            "The PDF format may have changed."
        )

    result = []
    year = base_year
    previous_month: int | None = None
    for (_, month), (_, days), zone_centres in zip(
        headings, date_columns, zones, strict=True
    ):
        if previous_month is not None and month < previous_month:
            year += 1
        result.append((year, month, days, zone_centres))
        previous_month = month
    return result


def _parse_page(page: LTPage, base_year: int, zone: str) -> list[Collection]:
    columns = _calendar_columns(page, base_year)
    zone_index = 0 if zone == "A" else 1
    zone_positions = [
        (column, index, centre)
        for column in columns
        for index, centre in enumerate(column[3])
    ]
    collections: dict[tuple[date, str], Collection] = {}

    for element in _iter_elements(page):
        if not isinstance(element, LTCurve) or not element.fill:
            continue
        waste_type = _waste_type(element.non_stroking_color)
        if waste_type is None:
            continue

        centre_x = (element.x0 + element.x1) / 2
        centre_y = (element.y0 + element.y1) / 2
        column, nearest_zone_index, zone_centre = min(
            zone_positions,
            key=lambda item: abs(item[2] - centre_x),
        )
        if (
            nearest_zone_index != zone_index
            or abs(zone_centre - centre_x) > _MAX_ZONE_DISTANCE
        ):
            continue

        day, day_y = min(column[2], key=lambda item: abs(item[1] - centre_y))
        if abs(day_y - centre_y) > _MAX_DAY_DISTANCE:
            continue

        collection_date = date(column[0], column[1], day)
        collections[(collection_date, waste_type)] = Collection(
            collection_date, waste_type, icon=ICON_MAP[waste_type]
        )

    return list(collections.values())


def _parse_pdf(content: bytes, zone: str) -> list[Collection]:
    pages = list(extract_pages(BytesIO(content)))
    if not pages:
        raise ValueError("The ETRA calendar PDF contains no pages.")

    base_year: int | None = None
    for page in pages:
        for element in page:
            if not isinstance(element, LTTextBoxHorizontal):
                continue
            if year_match := _YEAR_RE.search(element.get_text()):
                base_year = int(year_match.group(1))
                break
        if base_year is not None:
            break
    if base_year is None:
        raise ValueError(
            "Could not determine the schedule year from the ETRA calendar PDF."
        )

    collections: list[Collection] = []
    for page in pages:
        collections.extend(_parse_page(page, base_year, zone))

    unique = {(item.date, item.type): item for item in collections}
    return sorted(unique.values(), key=lambda item: (item.date, item.type))


def _find_pdf_url(html: str, document_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        if urlparse(href).path.casefold().endswith(".pdf"):
            return urljoin(document_url, href)
    raise ValueError(
        "No PDF attachment was found on the San Martino di Lupari ETRA page."
    )


class Source:
    def __init__(self, zone: str):
        normalized_zone = zone.strip().upper()
        if normalized_zone not in ("A", "B"):
            raise SourceArgumentNotFoundWithSuggestions("zone", zone, ["A", "B"])
        self._zone = normalized_zone

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)

        today = date.today()
        collections: list[Collection] = []
        document_responses: list[requests.Response] = []
        for document_year in (today.year, today.year - 1):
            document_url = _DOCUMENT_URL.format(year=document_year)
            document_response = session.get(document_url, timeout=30)
            document_responses.append(document_response)
            if document_response.status_code == 404:
                continue
            document_response.raise_for_status()
            pdf_url = _find_pdf_url(document_response.text, document_url)

            _LOGGER.debug("Downloading ETRA calendar from %s", pdf_url)
            pdf_response = session.get(pdf_url, timeout=60)
            pdf_response.raise_for_status()
            collections.extend(_parse_pdf(pdf_response.content, self._zone))

            # ETRA calendars span February through January. In January, merge
            # the prior year's calendar with the new one when both are
            # available; during the rest of the year the current calendar is
            # sufficient.
            if document_year == today.year and today.month != 1:
                break

        if not collections and all(
            response.status_code == 404 for response in document_responses
        ):
            document_responses[0].raise_for_status()
        if not collections:
            raise ValueError(
                f"No collections found for zone {self._zone} in the ETRA PDF. "
                "The PDF format may have changed."
            )
        unique = {(item.date, item.type): item for item in collections}
        return sorted(unique.values(), key=lambda item: (item.date, item.type))
