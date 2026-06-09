import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "City of Barrie"
DESCRIPTION = "Source for City of Barrie, Ontario, Canada."
URL = "https://www.barrie.ca/services-payments/garbage-recycling-organics/curbside-collection/collection-schedules"
COUNTRY = "ca"

TEST_CASES = {
    "Quance St": {"street_number": "47", "street_name": "Quance St"},
    "Kozlov St": {"street_number": "100", "street_name": "Kozlov St"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street number and street name as shown on the "
        "[Barrie collection schedule page]"
        "(https://www.barrie.ca/services-payments/garbage-recycling-organics/"
        "curbside-collection/collection-schedules). "
        "Abbreviate street suffixes (e.g. 'St' not 'Street', 'Ave' not 'Avenue')."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_number": "Street Number",
        "street_name": "Street Name",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_number": "Your house/street number",
        "street_name": "Street name with abbreviated suffix (e.g. 'Quance St')",
    },
}

FORM_URL = "https://sites.barrie.ca/barrieforms/Collection.aspx"
EVENTS_URL = "https://sites.barrie.ca/barrieforms/Scripts/collection_events.json"

DAY_ABBREVIATIONS = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday",
}

# Keywords to detect in compound summary strings, ordered longest-first
WASTE_COMPONENTS = [
    ("Yard Waste", "Yard Waste", "mdi:leaf"),
    ("Textile Collection", "Textile Collection", "mdi:tshirt-crew"),
    ("Battery", "Battery Collection", "mdi:battery"),
    ("Tree", "Christmas Tree", "mdi:pine-tree"),
    ("Garbage", "Garbage", "mdi:trash-can"),
    ("Recycling", "Recycling", "mdi:recycle"),
    ("Organics", "Organics", "mdi:food-apple"),
]

SKIP_SUMMARIES = {"Cart Notice"}


def _expand_day_abbreviation(area_code: str) -> str:
    """Expand day abbreviations in area codes (e.g. 'Wed Area B' -> 'Wednesday Area B')."""
    return re.sub(
        r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b",
        lambda m: DAY_ABBREVIATIONS.get(m.group(), m.group()),
        area_code,
    )


def _split_summary(summary: str) -> list[tuple[str, str]]:
    """Split a compound summary into (label, icon) pairs."""
    results = []
    for keyword, label, icon in WASTE_COMPONENTS:
        if keyword in summary:
            results.append((label, icon))
    return results


class Source:
    def __init__(self, street_number: str, street_name: str):
        self._street_number = str(street_number).strip()
        self._street_name = street_name.strip().upper()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1: GET the form to obtain ASP.NET ViewState
        r = session.get(FORM_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})

        form_data = {
            "__VIEWSTATE": viewstate["value"] if viewstate else "",
            "__VIEWSTATEGENERATOR": viewstate_gen["value"] if viewstate_gen else "",
            "__EVENTVALIDATION": event_validation["value"] if event_validation else "",
            "ctl00$MainContent$txtStreetNo": self._street_number,
            "ctl00$MainContent$txtStreet": self._street_name,
            "ctl00$MainContent$btnSubmit": "Submit",
        }

        # Step 2: POST to get the collection area
        r = session.post(FORM_URL, data=form_data, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        calendar_el = soup.find(id="MainContent_calendar_ID")
        if not calendar_el:
            raise SourceArgumentNotFound(
                "street_name",
                self._street_name,
                "no collection area found for this address.",
            )

        area_code = calendar_el.get_text(strip=True)
        if not area_code:
            raise SourceArgumentNotFound(
                "street_name",
                self._street_name,
                "no collection area found for this address.",
            )

        # Expand day abbreviations to match JSON keys
        area_key = _expand_day_abbreviation(area_code)

        # Step 3: Fetch the collection events JSON
        r = session.get(EVENTS_URL, timeout=30)
        r.raise_for_status()
        all_events = r.json()

        if area_key not in all_events:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name",
                f"{self._street_name} (area: {area_key})",
                list(all_events.keys()),
            )

        events = all_events[area_key]

        # Also include "No Location" events if present
        no_location = all_events.get("No Location", [])

        # Step 4: Parse events into collections
        entries: list[Collection] = []
        now = datetime.now().date()

        for event in events + no_location:
            summary = event.get("summary", "")
            if summary in SKIP_SUMMARIES:
                continue

            date = datetime.strptime(event["start"], "%Y-%m-%d").date()
            if date < now:
                continue

            components = _split_summary(summary)
            if not components:
                # Unknown summary — return as-is
                entries.append(Collection(date=date, t=summary))
            else:
                for label, icon in components:
                    entries.append(Collection(date=date, t=label, icon=icon))

        return entries
