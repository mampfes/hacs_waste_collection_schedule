import logging
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "City of Wanneroo"
DESCRIPTION = "Source for City of Wanneroo."
URL = "https://www.wanneroo.wa.gov.au/"
TEST_CASES = {
    "23 Bakana LP LANDSDALE": {"address": "23 Bakana LP LANDSDALE"},
    "13/26 Princeton CIR ALEXANDER HEIGHTS": {
        "address": "13/26 Princeton CIR ALEXANDER HEIGHTS"
    },
    "1 Atlanta DR TWO ROCKS": {"address": "1 Atlanta DR TWO ROCKS"},
    "23 Bakana Loop, Landsdale": {"address": "23 Bakana Loop, Landsdale"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Organics": Icons.GARDEN,
}

# The bin day lookup on
# https://www.wanneroo.wa.gov.au/residential-services/waste-and-recycling/bin-collections
# posts to these two endpoints (see /assets/modules/aw_bindaylookup.js).
ADDRESS_LOOKUP_URL = "https://www.wanneroo.wa.gov.au/spatial/addresslookup"
BINDAY_LOOKUP_URL = "https://www.wanneroo.wa.gov.au/spatial/bindaylookup"

# Response keys -> (waste type, weeks between collections). General waste is
# collected weekly; recycling and garden organics alternate fortnightly.
BIN_TYPES = {
    "generalWaste": ("General Waste", 1),
    "recycleWaste": ("Recycling", 2),
    "greenWaste": ("Garden Organics", 2),
}

# How many collections to project from the next collection date.
WEEKS_AHEAD = 12

TIMEZONE = ZoneInfo("Australia/Perth")

# The address lookup returns at most this many matches.
MAX_RESULTS = 10

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# The council's register stores abbreviated street types ("23 Bakana LP
# LANDSDALE"). Users typically spell them out; expand both sides before
# comparing so "23 Bakana Loop, Landsdale" matches the canonical entry.
STREET_TYPE_ABBREVIATIONS = {
    "ST": "STREET",
    "RD": "ROAD",
    "DR": "DRIVE",
    "DRV": "DRIVE",
    "AVE": "AVENUE",
    "AV": "AVENUE",
    "LP": "LOOP",
    "PL": "PLACE",
    "BVD": "BOULEVARD",
    "BLVD": "BOULEVARD",
    "CL": "CLOSE",
    "CT": "COURT",
    "CRES": "CRESCENT",
    "CR": "CRESCENT",
    "CIR": "CIRCLE",
    "CCT": "CIRCUIT",
    "GTE": "GATE",
    "PDE": "PARADE",
    "TCE": "TERRACE",
    "HWY": "HIGHWAY",
    "GRV": "GROVE",
    "GR": "GROVE",
    "LN": "LANE",
    "SQ": "SQUARE",
    "ESP": "ESPLANADE",
    "PWY": "PARKWAY",
    "PKWY": "PARKWAY",
    "PKY": "PARKWAY",
    "GDNS": "GARDENS",
    "WY": "WAY",
    "TRL": "TRAIL",
}


def _normalise_address(address: str) -> str:
    tokens = address.upper().replace(",", " ").split()
    return " ".join(STREET_TYPE_ABBREVIATIONS.get(t, t) for t in tokens)


def _reduced_queries(address: str) -> list[str]:
    """Progressively shorter search terms for a strict register search.

    The register search returns nothing for spelled-out street types or
    appended suburbs, but happily lists candidates for "23 Bakana" — which
    then feed the matching and suggestions flow.
    """
    tokens = address.upper().replace(",", " ").split()
    queries = []
    for cut in range(len(tokens) - 1, 0, -1):
        head = tokens[:cut]
        # Stop shrinking below "<number> <name>".
        if len(head) < 2:
            break
        if head[-1] in STREET_TYPE_ABBREVIATIONS or head[-1] in set(
            STREET_TYPE_ABBREVIATIONS.values()
        ):
            continue
        queries.append(" ".join(head))
    return queries[:2]


def _today() -> date:
    return datetime.now(TIMEZONE).date()


def _parse_display_date(display_date: str) -> date | None:
    """Fallback for when collectDate is missing: "Monday today",
    "Thursday this week", "Thursday next week", "Thursday week after next"."""
    text = display_date.strip().lower()
    today = _today()
    if "today" in text:
        return today
    if "tomorrow" in text:
        return today + timedelta(days=1)

    match = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
        r"\s+(this week|next week|week after next)",
        text,
    )
    if not match:
        return None
    week_start = today - timedelta(days=today.weekday())
    offset = {"this week": 0, "next week": 7, "week after next": 14}[match.group(2)]
    return week_start + timedelta(days=WEEKDAYS.index(match.group(1)) + offset)


def _next_collection(entry: dict) -> date | None:
    collect_date = entry.get("collectDate")
    if collect_date:
        try:
            parsed = datetime.fromisoformat(collect_date)
        except ValueError:
            parsed = None
        # "0001-01-01T00:00:00" is returned when the collection is today.
        if parsed is not None and parsed.year > 1:
            return parsed.date()

    display_date = entry.get("displayDate")
    if display_date:
        return _parse_display_date(display_date)
    return None


class Source:
    def __init__(self, address: str):
        self._address: str = address
        self._map_id: str | None = None
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
        )

    def _match_address(self, address: str) -> bool:
        return _normalise_address(self._address) == _normalise_address(address)

    def _search(self, query: str) -> list[dict]:
        r = self._session.post(ADDRESS_LOOKUP_URL, json={"address": query})
        r.raise_for_status()
        result = r.json()
        if not isinstance(result, list):
            return []
        return [e for e in result if isinstance(e, dict) and e.get("address")]

    def _queries(self) -> list[str]:
        queries = [self._address]
        if "/" not in self._address:
            # The lookup returns at most MAX_RESULTS matches, sorted by
            # address, so "23 Bakana LP" can be hidden behind
            # "1/23 Bakana LP" .. "18/23 Bakana LP". A unit number no
            # property has ("Z/23 ...") returns the property itself.
            queries.append(f"Z/{self._address}")
        for reduced in _reduced_queries(self._address):
            queries.append(reduced)
            if "/" not in reduced:
                queries.append(f"Z/{reduced}")
        return queries

    def _fetch_map_id(self) -> str:
        suggestions: list[str] = []
        for query in self._queries():
            for entry in self._search(query):
                address = entry["address"].strip()
                if self._match_address(address) and entry.get("mapId"):
                    return str(entry["mapId"])
                if address not in suggestions:
                    suggestions.append(address)

        if not suggestions:
            raise SourceArgumentNotFound("address", self._address)
        raise SourceArgumentNotFoundWithSuggestions(
            "address", self._address, suggestions
        )

    def fetch(self) -> list[Collection]:
        if not self._map_id:
            self._map_id = self._fetch_map_id()

        r = self._session.post(BINDAY_LOOKUP_URL, json={"mapId": self._map_id})
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise Exception("Unexpected response from the bin day lookup")

        entries: list[Collection] = []
        for key, (bin_type, interval) in BIN_TYPES.items():
            entry = data.get(key)
            if not isinstance(entry, dict):
                continue
            next_date = _next_collection(entry)
            if next_date is None:
                _LOGGER.warning(
                    "Could not read the %s collection date: %s", bin_type, entry
                )
                continue
            for d in rrule(
                WEEKLY,
                interval=interval,
                dtstart=datetime.combine(next_date, datetime.min.time()),
                count=WEEKS_AHEAD // interval,
            ):
                entries.append(
                    Collection(date=d.date(), t=bin_type, icon=ICON_MAP.get(bin_type))
                )

        if not entries:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "no bin collections are listed for this address",
            )
        return entries
