import base64
import datetime
import json
import re

from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "East Lindsey District Council"
DESCRIPTION = "Source for East Lindsey District Council waste collection."
URL = "https://www.e-lindsey.gov.uk"
TEST_CASES = {
    "13 Firbeck Avenue, Skegness": {"uprn": "100030786099"},
}

EXTRA_INFO = [
    {
        "title": TITLE,
        "url": URL,
        "country": "gb",
        "default_params": {},
    }
]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your UPRN using a tool like findmyaddress.co.uk or finders.io."
}

PARAM_DESCRIPTIONS = {"en": {"uprn": "Unique Property Reference Number (UPRN)"}}
PARAM_TRANSLATIONS = {"en": {"uprn": "UPRN"}}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
    "Purple Bin": "mdi:recycle",
}

_PAGE_URL = "https://www.e-lindsey.gov.uk/mywastecollections"
_SUBMIT_URL = "https://www.e-lindsey.gov.uk/mywastecollections/processsubmission"

_ORDINAL_RE = re.compile(r"(\d+)(st|nd|rd|th)")


def _parse_date(s: str) -> datetime.date | None:
    """Parse e.g. 'Wednesday 29th April 2026' → date."""
    if not s:
        return None
    s = _ORDINAL_RE.sub(r"\1", s)  # strip ordinal suffix
    parts = s.split()
    # format: "Weekday DD Month YYYY"
    if len(parts) == 4:
        try:
            return datetime.datetime.strptime(
                f"{parts[1]} {parts[2]} {parts[3]}", "%d %B %Y"
            ).date()
        except ValueError:
            pass
    return None


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome124")

        # Step 1: GET the page to extract form prefix and session tokens
        r = session.get(_PAGE_URL, timeout=30)
        r.raise_for_status()
        html = r.text

        # Extract form prefix (e.g. WASTECOLLECTIONDAYS202627)
        prefix_match = re.search(r'name="([A-Z0-9]+)_pageSessionId"', html)
        if not prefix_match:
            raise SourceArgumentNotFound(
                "uprn", self._uprn, "Could not find form prefix on page"
            )
        prefix = prefix_match.group(1)

        # Extract session tokens
        page_session_id = re.search(
            rf'name="{prefix}_pageSessionId"\s+value="([^"]+)"', html
        )
        fsid = re.search(rf'name="{prefix}_fsid"\s+value="([^"]+)"', html)
        fsn = re.search(rf'name="{prefix}_fsn"\s+value="([^"]+)"', html)

        if not all([page_session_id, fsid, fsn]):
            raise SourceArgumentNotFound(
                "uprn", self._uprn, "Could not extract form session tokens"
            )

        # Step 2: POST to processsubmission with UPRN
        variables = json.dumps({"UPRN": self._uprn})
        form_data = {
            f"{prefix}_pageSessionId": page_session_id.group(1),
            f"{prefix}_fsid": fsid.group(1),
            f"{prefix}_fsn": fsn.group(1),
            f"{prefix}_FIELD1": self._uprn,
            f"{prefix}_VARIABLES": variables,
            f"{prefix}_submit": "1",
        }

        r = session.post(_SUBMIT_URL, data=form_data, timeout=30)
        r.raise_for_status()

        # Step 3: Extract base64-encoded FIELD12 data from response JS
        data_match = re.search(
            rf'var\s+{prefix}_RESULTS_FIELD12Data\s*=\s*"([^"]+)"',
            r.text,
        )
        if not data_match:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection data found — check that the UPRN is valid",
            )

        decoded = base64.b64decode(data_match.group(1)).decode("utf-8")
        payload = json.loads(decoded)

        result_list = payload.get("RESULTS_1", {}).get("FIELD12", {}).get("result", [])
        if not result_list:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection results found — check that the UPRN is valid",
            )

        result = result_list[0]

        collections = []
        for field, waste_type in [
            ("wastenextref", "Refuse"),
            ("wastenextrec", "Recycling"),
            ("wastenextpur", "Purple Bin"),
            ("greenfirst", "Garden Waste"),
        ]:
            raw = result.get(field, "")
            date = _parse_date(raw)
            if date:
                collections.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                    )
                )

        return collections
