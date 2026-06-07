"""Source for Baltimore County Solid Waste Collection Schedule, US."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Baltimore County"
DESCRIPTION = "Source for Baltimore County Solid Waste Collection Schedule, US."
URL = "https://www.baltimorecountymd.gov/departments/public-works/solid-waste/collection-schedule"
COUNTRY = "us"

TEST_CASES = {
    "Towson": {"address": "309 W CHESAPEAKE AVE, TOWSON, MD, 21204"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to the Baltimore County collection schedule page, type your house number and "
        "street in the Address field, and select the full address from the dropdown (for "
        "example: 309 W CHESAPEAKE AVE, TOWSON, MD, 21204)."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Complete address selected from county suggestions (for example: 309 W CHESAPEAKE AVE, TOWSON, MD, 21204)",
    }
}

ICON_MAP = {
    "trash": Icons.GENERAL_WASTE,
    "garbage": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "recycle": Icons.RECYCLING,
    "yard": Icons.GARDEN,
    "yard material": Icons.GARDEN,
    "bulk": Icons.BULKY,
    "bulk item": Icons.BULKY,
    "organics": Icons.ORGANIC,
    "organic": Icons.ORGANIC,
}

AJAX_URL = f"{URL}?ajax_form=1&_wrapper_format=drupal_ajax"
TIMEOUT = 30
WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)


class Source:
    def __init__(self, address: str | None = None) -> None:
        self._address = address.strip() if isinstance(address, str) else ""
        if not self._address:
            raise SourceArgumentRequired(
                "address",
                "A complete address selected from the lookup suggestions is required.",
            )
        self._session = requests.Session(impersonate="chrome")

    def fetch(self) -> list[Collection]:
        page_html = self._load_page()
        form_state = self._extract_form_state(page_html)
        results_html = self._load_results_html(form_state)
        events = self._extract_events(results_html, page_html)

        if not events:
            raise SourceArgumentNotFound("address", self._address)

        collections = [
            Collection(date=event["date"], t=event["type"], icon=event["icon"])
            for event in events
            if event["date"] >= date.today()
        ]
        return sorted(collections, key=lambda item: (item.date, item.type))

    def _load_page(self) -> str:
        response = self._session.get(URL, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

    def _extract_form_state(self, page_html: str) -> dict[str, str]:
        soup = BeautifulSoup(page_html, "html.parser")
        address_field = soup.find("input", attrs={"name": "bcg_address"})
        if address_field is None:
            raise SourceArgumentNotFound("address", self._address)
        form = address_field.find_parent("form")
        if form is None:
            raise SourceArgumentNotFound("address", self._address)

        form_build_input = form.find("input", attrs={"name": "form_build_id"})
        form_id_input = form.find("input", attrs={"name": "form_id"})
        if form_build_input is None or form_id_input is None:
            raise SourceArgumentNotFound("address", self._address)

        libraries = ""
        match = re.search(r'"libraries":"([^"]+)"', page_html)
        if match:
            libraries = match.group(1).replace("\\/", "/")

        return {
            "form_build_id": str(form_build_input.get("value", "")),
            "form_id": str(form_id_input.get("value", "")),
            "theme": "gesso",
            "theme_token": "",
            "libraries": libraries,
        }

    def _load_results_html(self, form_state: dict[str, str]) -> str:
        payload = {
            "bcg_address": self._address,
            "form_build_id": form_state["form_build_id"],
            "form_id": form_state["form_id"],
            "_triggering_element_name": "find",
            "_triggering_element_value": "Find",
            "_drupal_ajax": "1",
            "ajax_page_state[theme]": form_state["theme"],
            "ajax_page_state[theme_token]": form_state["theme_token"],
            "ajax_page_state[libraries]": form_state["libraries"],
        }
        response = self._session.post(AJAX_URL, data=payload, timeout=TIMEOUT)
        response.raise_for_status()

        commands = json.loads(response.text)
        for command in commands:
            if command.get("command") == "insert":
                html = str(command.get("data", ""))
                if "collection_schedule_results_wrapper" in html:
                    return html

        raise SourceArgumentNotFound("address", self._address)

    def _extract_events(
        self, results_html: str, page_html: str
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(results_html, "html.parser")
        rows = soup.select("table tbody tr")
        events: list[dict[str, Any]] = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            waste_type = cells[0].get_text(" ", strip=True)
            frequency = cells[1].get_text(" ", strip=True)
            schedule_text = cells[2].get_text(" ", strip=True)
            icon = self._icon_for_type(waste_type)

            if "weekly" in frequency.casefold():
                weekday = self._weekday_from_text(schedule_text)
                if weekday is not None:
                    for event_date in self._next_weekly_dates(weekday, 12):
                        events.append(
                            {"date": event_date, "type": waste_type, "icon": icon}
                        )
                continue

            explicit_dates = self._extract_dates(schedule_text)
            if explicit_dates:
                for event_date in explicit_dates:
                    events.append(
                        {"date": event_date, "type": waste_type, "icon": icon}
                    )
                continue

            schedule_match = re.search(r"schedule\s*(\d)", frequency, re.IGNORECASE)
            weekday = self._weekday_from_text(schedule_text)
            if schedule_match and weekday is not None:
                schedule_id = schedule_match.group(1)
                for event_date in self._yard_schedule_dates(
                    page_html, schedule_id, weekday
                ):
                    events.append(
                        {"date": event_date, "type": waste_type, "icon": icon}
                    )

        deduped: dict[tuple[date, str], dict[str, Any]] = {}
        for event in events:
            deduped[(event["date"], event["type"])] = event
        return list(deduped.values())

    def _yard_schedule_dates(
        self, page_html: str, schedule_id: str, target_weekday: int
    ) -> list[date]:
        soup = BeautifulSoup(page_html, "html.parser")
        heading = soup.find(
            lambda tag: tag.name in ["h2", "h3", "h4"]
            and tag.get_text(strip=True).lower().endswith(f"schedule {schedule_id}")
        )
        if heading is None:
            return []

        table = heading.find_next("table")
        if table is None:
            return []

        dates: list[date] = []
        current_year = date.today().year
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            week_text = cells[1].get_text(" ", strip=True)
            for base_date in self._extract_dates(week_text, year=current_year):
                offset = (target_weekday - 6) % 7
                dates.append(base_date + timedelta(days=offset))
        return dates

    @staticmethod
    def _extract_dates(text: str, year: int | None = None) -> list[date]:
        matches = re.findall(
            rf"({MONTH_PATTERN}\s+\d{{1,2}}(?:,\s*\d{{4}})?)",
            text,
            flags=re.IGNORECASE,
        )
        parsed_dates: list[date] = []
        for match in matches:
            candidate = match.strip()
            if not re.search(r"\d{4}", candidate):
                if year is None:
                    continue
                candidate = f"{candidate}, {year}"
            try:
                parsed_dates.append(parse(candidate).date())
            except (TypeError, ValueError, OverflowError):
                continue
        return parsed_dates

    @staticmethod
    def _next_weekly_dates(weekday: int, count: int) -> list[date]:
        today = date.today()
        delta = (weekday - today.weekday()) % 7
        first_date = today + timedelta(days=delta)
        return [first_date + timedelta(days=7 * index) for index in range(count)]

    @staticmethod
    def _weekday_from_text(text: str) -> int | None:
        lowered = text.casefold()
        for name, idx in WEEKDAY_INDEX.items():
            if name in lowered:
                return idx
        return None

    def _icon_for_type(self, waste_type: str) -> str:
        normalized = waste_type.casefold()
        for key, icon in ICON_MAP.items():
            if key in normalized:
                return icon
        return Icons.GENERAL_WASTE
