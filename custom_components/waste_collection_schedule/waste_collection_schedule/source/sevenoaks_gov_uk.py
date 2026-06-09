import json
import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Sevenoaks District Council"
DESCRIPTION = "Source for Sevenoaks District Council waste collection schedule"
URL = "https://www.sevenoaks.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "1 Crawshay Close TN13 3EJ": {"property_id": 51621},
    "10 Mill Lane TN14 5BX": {"property_id": 15147},
}

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://sevenoaks-dc-host01.oncreate.app"
WEBPAGE_TOKEN = "978e3e1fd8936f98a424235001d93f261cc2458668d650a18f3a1155494d063d"
SUBPAGE_ID = "PAG0000639GBDJR1"
CELL_ID = "PCL0004972GBDJR1"
LANDING_PATH = "/w/webpage/waste-collection-day"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Section heading -> (waste type label, icon). Headings are matched
# case-insensitively as substrings of the rendered fragment headings.
SECTIONS = [
    ("Fortnightly garden waste collection", "Garden waste", Icons.GARDEN),
    (
        "Weekly recycling and general waste collection",
        "Recycling and general waste",
        Icons.GENERAL_WASTE,
    ),
    ("Weekly food waste collection", "Food waste", Icons.BIO_KITCHEN),
]

# Matches dates rendered as plain text, e.g. "Thursday 04 June 2026".
DATE_RE = re.compile(
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]+ (\d{1,2} [A-Z][a-z]+ \d{4})"
)

ICON_MAP = {
    "Garden waste": Icons.GARDEN,
    "Recycling and general waste": Icons.GENERAL_WASTE,
    "Food waste": Icons.BIO_KITCHEN,
}

PARAM_TRANSLATIONS = {
    "en": {
        "property_id": "Property ID",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "property_id": "Internal numeric property identifier from Sevenoaks' waste collection day lookup (e.g. 51621)",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://sevenoaks-dc-host01.oncreate.app/w/webpage/waste-collection-day, enter your postcode (with the space), select your address; the numeric property id is the `id=` value in the resulting page URL.",
}


class Source:
    def __init__(self, property_id: int | str):
        self._property_id = str(property_id)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        # Step 1: initialise the session (sets the GBDJR3-mats_session cookie).
        session.get(f"{BASE_URL}{LANDING_PATH}").raise_for_status()

        # Step 2: select the address. The API mints a per-request schedule URL
        # (with fresh expiry/auth/id tokens) which must be used as-is.
        event_url = (
            f"{BASE_URL}{LANDING_PATH}"
            f"?webpage_subpage_id={SUBPAGE_ID}"
            f"&webpage_token={WEBPAGE_TOKEN}"
            f"&widget_action=handle_event"
        )
        r_select = session.post(
            event_url,
            data={
                "code_action": "address_selected",
                "code_params": json.dumps({"selected": self._property_id}),
                "action_cell_id": CELL_ID,
                "action_page_id": SUBPAGE_ID,
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        r_select.raise_for_status()
        select_json = r_select.json()

        schedule_url = select_json.get("response", {}).get("url")
        if select_json.get("result") != "success" or not schedule_url:
            raise SourceArgumentNotFound(
                "property_id",
                self._property_id,
                "the address lookup did not return a schedule URL — please check your property_id is correct",
            )

        # Step 3: fetch the schedule. This must be the first hit to the minted
        # URL with no extra query parameters, otherwise the server returns 403.
        r_schedule = session.get(
            schedule_url, headers={"X-Requested-With": "XMLHttpRequest"}
        )
        r_schedule.raise_for_status()
        html = r_schedule.json().get("data", "")

        return self._parse_schedule(html)

    def _parse_schedule(self, html: str) -> list[Collection]:
        if not html:
            raise SourceArgumentNotFound(
                "property_id",
                self._property_id,
                "no collection data returned — please check your property_id is correct",
            )

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        entries: list[Collection] = []
        for heading, waste_type, icon in SECTIONS:
            idx = text.lower().find(heading.lower())
            if idx == -1:
                continue
            segment = text[idx:]
            # Limit the segment to this section by stopping at the next heading.
            for other_heading, _, _ in SECTIONS:
                if other_heading == heading:
                    continue
                other_idx = segment.lower().find(other_heading.lower())
                if other_idx != -1:
                    segment = segment[:other_idx]
            match = DATE_RE.search(segment)
            if not match:
                continue
            try:
                next_date = datetime.strptime(match.group(1), "%d %B %Y").date()
            except ValueError:
                LOGGER.warning(
                    "Could not parse date %r for %r", match.group(1), waste_type
                )
                continue
            entries.append(Collection(date=next_date, t=waste_type, icon=icon))

        if not entries:
            raise SourceArgumentNotFound(
                "property_id",
                self._property_id,
                "no collection dates found — the address may not have a domestic waste collection service, or the property_id is incorrect",
            )

        return entries
