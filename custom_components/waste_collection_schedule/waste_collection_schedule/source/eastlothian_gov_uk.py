import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "East Lothian"
DESCRIPTION = "Source for East Lothian waste collection."
URL = "https://www.eastlothian.gov.uk/"
TEST_CASES = {
    "EH21 8GU 4 Laing Loan, Wallyford": {
        "postcode": "EH21 8GU",
        "address": "4 Laing Loan, Wallyford",
    },
    "EH41 4LN Peterhouse, Morham, Haddington": {
        "postcode": "EH41 4LN",
        "address": "Peterhouse, Morham, Haddington",
    },
    "1 Colliers Row Wallyford": {
        "postcode": "EH21 8GX",
        "address": "1 Colliers Row, Wallyford",
    },
}
_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "non recyclable waste": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "recycling": "mdi:recycle",
    "food waste": "mdi:food",
}

BASE_URL = "https://collectiondates.eastlothian.gov.uk"
SCHEDULE_URL = f"{BASE_URL}/waste-collection-schedule"


class Source:
    def __init__(
        self,
        postcode: str | None = None,
        address: str | None = None,
    ):
        self._postcode: str | None = postcode.strip() if postcode else None
        self._address: str | None = address.strip() if address else None

        if not self._postcode or not self._address:
            raise ValueError("postcode and address required")

    def _normalize(self, s: str) -> str:
        return " ".join(s.lower().replace(",", " ").split())

    def _address_match(self, option_text: str) -> bool:
        g_norm = self._normalize(self._address)
        o_norm = self._normalize(option_text)

        if g_norm == o_norm:
            return True
        if g_norm in o_norm:
            return True
        # Remove postcode from option if present
        o_parts = o_norm.split()
        if len(o_parts) > 3:
            o_without_postcode = " ".join(o_parts[:-2])
            if g_norm == o_without_postcode:
                return True
        return False

    def _resolve_address_id(self, session: requests.Session) -> str:
        r = session.get(SCHEDULE_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form_build_id_input = soup.find("input", {"name": "form_build_id"})
        if not isinstance(form_build_id_input, Tag):
            raise ValueError("Could not find form_build_id on schedule page")
        form_build_id = form_build_id_input["value"]

        data = {
            "postcode": self._postcode,
            "form_build_id": form_build_id,
            "form_id": "localgov_waste_collection_postcode_form",
            "op": "Find",
        }
        r = session.post(SCHEDULE_URL, data=data, allow_redirects=True)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", {"name": "uprn"})
        if not isinstance(select, Tag):
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "No address options found for postcode",
            )

        options = select.find_all("option")
        for option in options:
            if self._address_match(option.text):
                return str(option["value"])

        available = [opt.text for opt in options if opt.get("value")]
        raise SourceArgumentNotFoundWithSuggestions("address", self._address, available)

    def _get_ics(self, session: requests.Session, uprn: str) -> str:
        url = f"{BASE_URL}/waste-collection-schedule/download/{uprn}"
        r = session.get(url)
        r.raise_for_status()
        return r.text

    def _parse_ics(self, ics_data: str) -> list[Collection]:
        events: list[Collection] = []
        vevent_blocks = re.findall(
            r"BEGIN:VEVENT\r?\n(.*?)END:VEVENT", ics_data, re.DOTALL
        )

        for block in vevent_blocks:
            summary_match = re.search(r"SUMMARY:([^\r\n]+)", block)
            if not summary_match:
                continue
            summary = summary_match.group(1).strip()

            # Skip non-collection events
            if "download" in summary.lower() or "calendar" in summary.lower():
                continue

            # Extract DTSTART
            dtstart_match = re.search(r"DTSTART;TZID=[^:]+:(\d{8})T\d{6}", block)
            if not dtstart_match:
                dtstart_match = re.search(r"DTSTART:(\d{8})T", block)
            if not dtstart_match:
                dtstart_match = re.search(r"DTSTART[^:]*:(\d{8})", block)
            if not dtstart_match:
                continue

            date_str = dtstart_match.group(1)
            d = datetime.strptime(date_str, "%Y%m%d").date()

            # Clean up summary to extract waste type
            type_str = summary
            if " for " in summary:
                type_str = summary.split(" for ", 1)[1]
            type_str = type_str.strip()

            # Split combined types (e.g. "Food waste and recycling")
            if " and " in type_str.lower():
                parts = type_str.split(" and ")
                for part in parts:
                    part = part.strip()
                    icon = ICON_MAP.get(part.lower())
                    events.append(Collection(date=d, t=part, icon=icon))
            else:
                icon = ICON_MAP.get(type_str.lower())
                events.append(Collection(date=d, t=type_str, icon=icon))

        return events

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        uprn = self._resolve_address_id(session)
        ics_data = self._get_ics(session, uprn)
        return self._parse_ics(ics_data)
