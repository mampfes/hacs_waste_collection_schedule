"""Local Waste Services provider for Columbus-area municipalities.

This provider supports official Local Waste Services service-guidelines pages and
can optionally resolve a community page from the residential-services directory.
It focuses on the common public patterns visible on the official pages:

- collection day and materials-out time
- holiday-shifted weekly trash collection
- weekly recycling service
- biweekly recycling PDFs with route/zone sections
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from collections.abc import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound, SourceArgumentRequired

TITLE = "Local Waste Services (Central Ohio)"
DESCRIPTION = "Source for official Local Waste Services service-guidelines pages."
URL = "https://localwasteservices.com/services/residential-services"

TEST_CASES = {
    "City of Gahanna - Monday": {
        "url": "https://localwasteservices.com/service-guidelines/city-of-gahanna---monday"
    },
    "City of Hilliard": {
        "url": "https://localwasteservices.com/service-guidelines/city-of-hilliard"
    },
    "Clinton Township": {"url": "https://localwasteservices.com/service-guidelines/clinton-township"},
}

_LOGGER = logging.getLogger(__name__)

_WEEKDAY_TO_INT = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
_TIME_RE = re.compile(r"\b(\d{1,2}:\d{2}\s*[AP]M)\b", re.IGNORECASE)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _text_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]


def _resolve_service_url_from_directory(directory_html: str, community_name: str, directory_url: str) -> str:
    soup = BeautifulSoup(directory_html, "html.parser")
    matches: list[str] = []
    for anchor in soup.find_all("a", href=True):
        label = _clean_text(anchor.get_text(" ", strip=True))
        if community_name.lower() in label.lower():
            matches.append(urljoin(directory_url, anchor["href"]))
    if not matches:
        raise SourceArgumentNotFound("community_name", community_name)
    return matches[0]


def _parse_date_token(token: str, default_year: int | None = None) -> dt.date:
    month, day, year = token.split("/")
    year_i = int(year)
    if year_i < 100:
        year_i += 2000
    if len(year) == 2 and default_year is not None:
        year_i = default_year
    return dt.date(year_i, int(month), int(day))


def _extract_holiday_dates(lines: Iterable[str]) -> list[dt.date]:
    holidays: list[dt.date] = []
    for line in lines:
        for token in _DATE_RE.findall(line):
            holidays.append(_parse_date_token(token))
    return holidays


def _parse_service_page(html: str, page_url: str) -> dict[str, object]:
    lines = _text_lines(html)
    lowered = [line.lower() for line in lines]

    def _find_after(marker: str) -> str | None:
        marker_l = marker.lower()
        for idx, line in enumerate(lowered):
            if line == marker_l and idx + 1 < len(lines):
                return _clean_text(lines[idx + 1])
        return None

    collection_day = _find_after("Collection Day")
    materials_out_by = _find_after("Materials out by")
    recycling_pdf_url = None

    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.lower().endswith(".pdf"):
            recycling_pdf_url = urljoin(page_url, href)
            break

    recycling_mode = None
    for idx, line in enumerate(lowered):
        if line == "recycling":
            for next_line in lines[idx + 1 : idx + 5]:
                text = next_line.lower()
                if "biweekly" in text:
                    recycling_mode = "biweekly"
                    break
                if "weekly" in text:
                    recycling_mode = "weekly"
                    break
            if recycling_mode:
                break

    holidays = _extract_holiday_dates(lines)

    return {
        "collection_day": collection_day,
        "materials_out_by": materials_out_by,
        "holiday_dates": holidays,
        "recycling_mode": recycling_mode,
        "recycling_pdf_url": recycling_pdf_url,
    }


def _build_weekly_pickup_dates(
    start_date: dt.date,
    end_date: dt.date,
    collection_day: str,
    holiday_dates: Iterable[dt.date],
) -> list[dt.date]:
    target_weekday = _WEEKDAY_TO_INT[collection_day.lower()]
    holidays = {d for d in holiday_dates}
    dates: list[dt.date] = []
    current = start_date
    while current <= end_date:
        if current.weekday() == target_weekday:
            pickup_date = current
            week_start = pickup_date - dt.timedelta(days=(pickup_date.weekday() + 1) % 7)
            if any(
                week_start <= holiday <= pickup_date and holiday.weekday() < 5
                for holiday in holidays
            ):
                pickup_date = pickup_date + dt.timedelta(days=1)
            dates.append(pickup_date)
        current += dt.timedelta(days=1)
    return dates


def _parse_biweekly_pdf_text(pdf_text: str, default_year: int | None = None) -> dict[str, list[dt.date]]:
    lines = [line.strip() for line in pdf_text.splitlines() if line.strip()]
    year = default_year
    for line in lines:
        match = re.search(r"\b(20\d{2})\b", line)
        if match:
            year = int(match.group(1))
            break

    sections: dict[str, list[dt.date]] = {}
    current_section: str | None = None
    for line in lines:
        if "Collection Days" in line or "Collection Schedule" in line:
            current_section = _clean_text(line)
            sections.setdefault(current_section, [])
            continue
        if current_section is None:
            continue
        tokens = []
        for token in re.findall(r"\b(\d{1,2}/\d{1,2})(?:\s*\([A-Za-z]{3}\))?", line):
            tokens.append(token)
        if tokens:
            for token in tokens:
                month, day = token.split("/")
                sections[current_section].append(dt.date(year or dt.date.today().year, int(month), int(day)))
    return sections


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Placeholder for future PDF parsing support.

    The current MVP focuses on the common weekly service-guidelines pages.
    Biweekly PDF-backed routes are not yet parsed in the live provider.
    """
    _ = pdf_bytes
    return ""


class Source:
    def __init__(self, url: str | None = None, community_name: str | None = None):
        if url is None:
            raise SourceArgumentRequired("url", "official Local Waste Services page URL is required")
        self._url = url
        self._community_name = community_name

    def fetch(self) -> list[Collection]:
        with requests.Session() as session:
            service_url = self._url
            if "residential-services" in service_url:
                if not self._community_name:
                    raise SourceArgumentRequired(
                        "community_name",
                        "required when the URL points to the residential-services directory page",
                    )
                response = session.get(service_url, timeout=30)
                response.raise_for_status()
                service_url = _resolve_service_url_from_directory(
                    response.text, self._community_name, service_url
                )

            response = session.get(service_url, timeout=30)
            response.raise_for_status()
            parsed = _parse_service_page(response.text, service_url)

            collection_day = parsed["collection_day"]
            if not collection_day:
                raise ValueError(f"Could not find collection day on {service_url}")

            holidays = parsed["holiday_dates"]
            today = dt.date.today()
            end_date = today + dt.timedelta(days=365)
            entries: list[Collection] = []

            trash_dates = _build_weekly_pickup_dates(today, end_date, collection_day, holidays)
            for pickup_date in trash_dates:
                entries.append(
                    Collection(date=pickup_date, t="Trash", icon=Icons.GENERAL_WASTE)
                )

            recycling_mode = parsed["recycling_mode"]
            if recycling_mode == "weekly":
                for pickup_date in trash_dates:
                    entries.append(
                        Collection(date=pickup_date, t="Recycling", icon=Icons.RECYCLING)
                    )
            elif recycling_mode == "biweekly" and parsed["recycling_pdf_url"]:
                pdf_response = session.get(parsed["recycling_pdf_url"], timeout=30)
                pdf_response.raise_for_status()
                pdf_text = _extract_pdf_text(pdf_response.content)
                section_dates = _parse_biweekly_pdf_text(pdf_text)
                for section_name, dates in section_dates.items():
                    for pickup_date in dates:
                        entries.append(
                            Collection(
                                date=pickup_date,
                                t="Recycling",
                                icon=Icons.RECYCLING,
                                location=section_name,
                            )
                        )

            order = {"Trash": 0, "Recycling": 1}
            return sorted(entries, key=lambda item: (item.date, order.get(item.type, 99), item.location or ""))
