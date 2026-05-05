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

_ORDINAL_RE = re.compile(r"(\d+)(st|nd|rd|th)")


def _parse_date(s: str) -> datetime.date | None:
    """Parse e.g. 'Wednesday 29th April 2026' → date."""
    if not s:
        return None
    s = _ORDINAL_RE.sub(r"\1", s)
    parts = s.split()
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
        prefix_match = re.search(r'name="([A-Z0-9]+)_PAGESESSIONID"', html)
        if not prefix_match:
            raise SourceArgumentNotFound(
                "uprn", self._uprn, "Could not find form prefix on page"
            )
        prefix = prefix_match.group(1)

        # Extract form action URL (contains pageSessionId, fsid, fsn as query params)
        action_match = re.search(
            r'<form[^>]+action="(https://[^"]+/processsubmission[^"]*)"', html
        )
        if not action_match:
            raise SourceArgumentNotFound(
                "uprn", self._uprn, "Could not find form action URL on page"
            )
        submit_url = action_match.group(1).replace("&amp;", "&")

        # Extract hidden session tokens
        pagesid_match = re.search(
            rf'name="{prefix}_PAGESESSIONID"\s+value="([^"]+)"', html
        )
        sessionid_match = re.search(
            rf'name="{prefix}_SESSIONID"\s+value="([^"]+)"', html
        )
        nonce_match = re.search(rf'name="{prefix}_NONCE"\s+value="([^"]+)"', html)

        if not pagesid_match or not sessionid_match or not nonce_match:
            raise SourceArgumentNotFound(
                "uprn", self._uprn, "Could not extract form session tokens"
            )

        # Step 2: POST to processsubmission with UPRN in base64-encoded VARIABLES
        # ADDRESSSOURCE must be NLPGEL (National Land and Property Gazetteer for East Lindsey)
        variables = base64.b64encode(
            json.dumps(
                {
                    "ADDRESSSOURCE": {
                        "value": "NLPGEL",
                        "scope": "SERVERCLIENTWITHUPDATE",
                    },
                    "ADDRESSUPRN": {
                        "value": self._uprn,
                        "scope": "SERVERCLIENTWITHUPDATE",
                    },
                    "TESTDATELAYOUT_DISPLAYED": {
                        "value": False,
                        "scope": "SERVERCLIENT",
                    },
                }
            ).encode()
        ).decode()

        form_data = {
            f"{prefix}_PAGESESSIONID": pagesid_match.group(1),
            f"{prefix}_SESSIONID": sessionid_match.group(1),
            f"{prefix}_NONCE": nonce_match.group(1),
            f"{prefix}_VARIABLES": variables,
            f"{prefix}_PAGENAME": "LOOKUP",
            f"{prefix}_PAGEINSTANCE": "0",
            f"{prefix}_LOOKUP_CHOSENADDRESS": self._uprn,
            f"{prefix}_FORMACTION_NEXT": f"{prefix}_LOOKUP_FIELD2",
        }

        r = session.post(submit_url, data=form_data, timeout=30)
        r.raise_for_status()

        # Step 3: Parse FormData from the results page
        data_match = re.search(
            rf"{prefix}FormData\s*=\s*\"([^\"]+)\"",
            r.text,
        )
        if not data_match:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection data found — check that the UPRN is valid",
            )

        payload = json.loads(base64.b64decode(data_match.group(1)).decode("utf-8"))

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
