import re
import time
from datetime import date
from html import unescape

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
)

TEST_CASES = {
    "1 Coningsby Drive, Watford": {
        "uprn": "100080932722",
    }
}

TITLE = "Watford Borough Council"
DESCRIPTION = "Source for waste collection services for Watford Borough Council"
URL = "https://www.watford.gov.uk/"

BASE_URL = "https://watfordbc-self.achieveservice.com"
INITIAL_URL = f"{BASE_URL}/en/service/Bin_Collections?accept=yes&consentMessageIds[]=9"
API_URL = f"{BASE_URL}/apibroker/runLookup"

LOOKUP_ADDRESS_POINT = "5e57d2f638e6d"
LOOKUP_NEXT_COLLECTIONS = "5e79edf15b2ec"
LOOKUP_CALENDAR = "6750598d8b177"
FORM_ID = "AF-Form-a139d516-46fc-4e1d-a94e-5e072681bcf0"
REQUEST_TIMEOUT = 30

ICON_MAP = {
    "garden": "mdi:leaf",
    "black": "mdi:trash-can",
    "non-recyclable": "mdi:trash-can",
    "blue-lidded": "mdi:recycle",
    "recycling": "mdi:recycle",
    "brown": "mdi:food",
    "food": "mdi:food",
}


class Source:
    """Watford source.

    Watford's public postcode lookup currently appears unreliable/broken when called
    directly, but once the property token / UPRN is known the subsequent collection
    lookups work consistently.

    Preferred argument:
      - uprn: property UPRN / selected address value from the Watford form

    Optional:
      - address: explicit selected address token from the Watford form
    """

    def __init__(self, uprn: str | int | None = None, address: str | int | None = None):
        self._uprn = str(uprn).strip() if uprn is not None else None
        self._address = str(address).strip() if address is not None else None
        self._session = requests.Session()

        if not self._uprn and not self._address:
            raise SourceArgumentExceptionMultiple(
                ["uprn", "address"],
                "Either uprn or address must be provided.",
            )

    def _init_session(self) -> str:
        r = self._session.get(INITIAL_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        match = re.search(r'"auth-session":"([^"]+)"', r.text)
        if not match:
            raise ValueError("Failed to obtain Watford auth session")
        return match.group(1)

    def _run_lookup(self, sid: str, lookup_id: str, form_values: dict) -> dict:
        params = {
            "id": lookup_id,
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": str(int(time.time() * 1000)),
            "sid": sid,
        }
        payload = {"formId": FORM_ID, "formValues": form_values}
        r = self._session.post(
            API_URL, params=params, json=payload, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        data = r.json()
        transformed = data.get("integration", {}).get("transformed", {})
        if data.get("status") == "error" or transformed.get("error"):
            raise ValueError(
                f"Watford lookup {lookup_id} failed: {data.get('error') or transformed.get('error') or data.get('data')}"
            )
        return transformed

    def _resolve_identifiers(self, sid: str) -> tuple[str, str, str]:
        address_token = self._address or self._uprn
        uprn_value = self._uprn or self._address
        # Normalise UPRN once: strip leading zeros for the echoUprn field and
        # reuse the same normalised value in all subsequent lookups.
        normalised_uprn = str(uprn_value).lstrip("0")
        transformed = self._run_lookup(
            sid,
            LOOKUP_ADDRESS_POINT,
            {
                "Address": {
                    "echoUprn": {"value": normalised_uprn},
                    "address": {"value": str(address_token)},
                }
            },
        )
        row = transformed.get("rows_data", {}).get("0", {})
        echo_address_point = row.get("echoAddressPoint")
        if not echo_address_point:
            raise ValueError("Watford source could not resolve echoAddressPoint")
        return str(address_token), normalised_uprn, str(echo_address_point)

    def _fetch_collections(
        self, sid: str, address_token: str, uprn_value: str, echo_address_point: str
    ) -> dict:
        return self._run_lookup(
            sid,
            LOOKUP_NEXT_COLLECTIONS,
            {
                "Address": {
                    "address": {"value": address_token},
                    "echoUprn": {"value": uprn_value},
                    "echoAddressPoint": {"value": echo_address_point},
                }
            },
        )

    def _fetch_calendar(
        self, sid: str, address_token: str, uprn_value: str, echo_address_point: str
    ) -> dict:
        return self._run_lookup(
            sid,
            LOOKUP_CALENDAR,
            {
                "Address": {
                    "address": {"value": address_token},
                    "echoUprn": {"value": uprn_value},
                    "echoAddressPoint": {"value": echo_address_point},
                }
            },
        )

    def _extract_collections_from_html(self, html_text: str) -> list[Collection]:
        html_text = unescape(html_text)
        items = re.findall(
            r'<li class="binItem">(.*?)</li>', html_text, flags=re.DOTALL
        )
        entries = []

        for item in items:
            title_match = re.search(r"<h3>(.*?)</h3>", item, flags=re.DOTALL)
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", item)
            if not title_match or not date_match:
                continue

            waste_type = re.sub(r"\s+", " ", unescape(title_match.group(1))).strip()
            day, month, year = date_match.group(1).split("/")
            icon = None
            lowered = waste_type.lower()
            for token, mapped_icon in ICON_MAP.items():
                if token in lowered:
                    icon = mapped_icon
                    break

            entries.append(
                Collection(
                    date=date(int(year), int(month), int(day)),
                    t=waste_type,
                    icon=icon,
                )
            )

        return entries

    def fetch(self) -> list[Collection]:
        sid = self._init_session()
        address_token, uprn_value, echo_address_point = self._resolve_identifiers(sid)

        collections_data = self._fetch_collections(
            sid, address_token, uprn_value, echo_address_point
        )

        row = collections_data.get("rows_data", {}).get("0", {})
        html_text = row.get("dispHTML", "")
        entries = self._extract_collections_from_html(html_text)

        if entries:
            return entries

        # Report errors against whichever argument the user actually configured.
        arg = "uprn" if self._uprn else "address"

        # Only fetch the calendar when needed (to diagnose why no entries were returned).
        if row.get("lastCollection") == "NaN-aN-aN":
            calendar_data = self._fetch_calendar(
                sid, address_token, uprn_value, echo_address_point
            )
            calendar = calendar_data.get("rows_data", {}).get("0", {}).get("calendar")
            raise SourceArgumentException(
                arg,
                f"Watford did not return collection data for this property token (calendar: {calendar or 'unknown'}).",
            )

        raise SourceArgumentException(
            arg,
            "Watford returned an unexpected response for this property token.",
        )
