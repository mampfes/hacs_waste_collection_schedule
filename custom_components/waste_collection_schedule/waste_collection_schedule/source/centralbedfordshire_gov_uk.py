import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Central Bedfordshire Council"
DESCRIPTION = (
    "Source for www.centralbedfordshire.gov.uk services for Central Bedfordshire"
)
URL = "https://www.centralbedfordshire.gov.uk"

TEST_CASES = {
    "postcode has space": {"postcode": "SG15 6YF", "house_name": "10 Old School Walk"},
    "postcode without space": {
        "postcode": "SG180LL",
        "house_name": "1 Chestnut Avenue",
    },
    "uprn direct": {"uprn": "10000863589"},
}

ICON_MAP = {
    "Refuse (black bin)": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden waste": Icons.GARDEN,
    "Food waste": Icons.BIO_KITCHEN,
}

_BASE_URL = "https://www.centralbedfordshire.gov.uk"
_FORM_URL = f"{_BASE_URL}/waste-and-recycling/waste-collection-schedule"
_ICAL_URL_TMPL = (
    f"{_BASE_URL}/waste-and-recycling/waste-collection-schedule/download/{{uprn}}"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

# Multi-value summaries like "Refuse (black bin) and food waste collections"
# split into individual canonical bin names via longest-match on this table.
# Ordered longest-first so "Refuse (black bin)" matches before "Refuse".
_BIN_ALIASES: list[tuple[str, str]] = [
    ("refuse (black bin)", "Refuse (black bin)"),
    ("black bin", "Refuse (black bin)"),
    ("refuse", "Refuse (black bin)"),
    ("recycling", "Recycling"),
    ("garden waste", "Garden waste"),
    ("food waste", "Food waste"),
]


def _split_summary(summary: str) -> list[str]:
    """Convert one iCal SUMMARY into a list of canonical bin names.

    Unknown fragments (e.g. the calendar-expiry reminder event) return [].

    Examples:
        "Refuse (black bin) and food waste collections"
            -> ["Refuse (black bin)", "Food waste"]
        "Recycling, garden waste and food waste collections"
            -> ["Recycling", "Garden waste", "Food waste"]
        "Garden Waste Collection"
            -> ["Garden waste"]
        "Download your bin collection calendar"
            -> []
    """
    text = summary.strip().lower()
    # remove trailing "collection"/"collections"
    text = re.sub(r"\s+collections?\s*$", "", text)
    # normalise separators (" and ", commas) into a single delimiter
    parts = re.split(r"\s*,\s*|\s+and\s+", text)
    result: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for needle, canon in _BIN_ALIASES:
            if needle in part:
                result.append(canon)
                break
        # Unknown fragments are silently dropped — the council emits non-collection
        # reminder events (e.g. "Download your bin collection calendar") that must
        # not become fake entries.
    return result


class Source:
    def __init__(
        self,
        postcode: str | None = None,
        house_name: str | None = None,
        uprn: str | int | None = None,
    ):
        if uprn is None and not (postcode and house_name):
            raise SourceArgumentRequiredWithSuggestions(
                "uprn",
                None,
                ["Provide `uprn` OR both `postcode` and `house_name`."],
            )
        self._postcode = postcode
        self._house_name = house_name
        self._uprn: str | None = str(uprn) if uprn is not None else None

    def _resolve_uprn(self, session: requests.Session) -> str:
        """Look up UPRN by scraping the council's postcode form (Drupal LocalGov)."""
        # Step 1 — GET the form to obtain the CSRF-like form_build_id + cookies
        r = session.get(_FORM_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        postcode_form = soup.find(id="localgov-waste-collection-postcode-form")
        if postcode_form is None:
            raise RuntimeError(
                "Postcode form not found on council page — layout may have changed."
            )
        fbid_input = postcode_form.find("input", attrs={"name": "form_build_id"})
        if fbid_input is None:
            raise RuntimeError("Postcode form is missing form_build_id.")

        # Step 2 — POST the postcode
        r = session.post(
            _FORM_URL,
            data={
                "postcode": self._postcode,
                "form_build_id": fbid_input["value"],
                "form_id": "localgov_waste_collection_postcode_form",
                "op": "Find",
            },
            timeout=30,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")
        addr_select = soup.find("select", attrs={"name": "uprn"})
        if addr_select is None:
            raise RuntimeError(
                "Address dropdown not found — postcode may be invalid or the page structure has changed."
            )

        # Build {label: uprn} map, then prefix-match against house_name
        addresses: dict[str, str] = {}
        for opt in addr_select.find_all("option"):
            val = (opt.get("value") or "").strip()
            if not val:
                continue
            addresses[opt.get_text(strip=True)] = val

        target = self._house_name.strip().lower()
        for label, uprn in addresses.items():
            if label.lower().startswith(target):
                return uprn

        raise SourceArgumentNotFoundWithSuggestions(
            "house_name", self._house_name, set(addresses.keys())
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)

        # Resolve UPRN once, then reuse for subsequent fetches.
        if self._uprn is None:
            self._uprn = self._resolve_uprn(session)

        # Fetch the per-UPRN iCal feed — this is the stable, structured endpoint.
        r = session.get(_ICAL_URL_TMPL.format(uprn=self._uprn), timeout=30)
        r.raise_for_status()

        events = ICS().convert(r.text)

        # Dedupe (date, bin_name) — the council emits both a standalone
        # "Garden Waste Collection" event AND a combined "Recycling, garden
        # waste and food waste collections" event on the same day for
        # addresses subscribed to the paid garden-waste service.
        seen: set[tuple] = set()
        entries: list[Collection] = []
        for date, summary in events:
            for bin_name in _split_summary(summary):
                key = (date, bin_name)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(
                        date=date, t=bin_name, icon=ICON_MAP.get(bin_name)
                    )
                )
        return entries
