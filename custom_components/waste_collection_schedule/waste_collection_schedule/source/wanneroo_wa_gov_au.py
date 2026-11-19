from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "City of Wanneroo"
DESCRIPTION = "Source for City of Wanneroo."
URL = "https://www.wanneroo.wa.gov.au/"
TEST_CASES = {
    "1 Atlanta DR TWO ROCKS": {"address": "1 Atlanta DR TWO ROCKS"},
    "13/26 Princeton CIR ALEXANDER HEIGHTS": {
        "address": "13/26 Princeton CIR ALEXANDER HEIGHTS"
    },
    "99 Two Rocks RD TWO ROCKS": {"address": "99 Two Rocks RD TWO ROCKS"},
}

ICON_MAP = {
    "Recycling": Icons.RECYCLING,
    "General Waste": Icons.GENERAL_WASTE,
    "Garden Organics": Icons.GARDEN,
}

# The council's address and bin-day lookups. The bin-day lookup returns the
# next collection date of each bin; only those dates are returned.
ADDRESS_URL = "https://www.wanneroo.wa.gov.au/spatial/addresslookup"
BINDAY_URL = "https://www.wanneroo.wa.gov.au/spatial/bindaylookup"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
}

# bin-day lookup key -> collection type
BINS = {
    "generalWaste": "General Waste",
    "recycleWaste": "Recycling",
    "greenWaste": "Garden Organics",
}

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
    "GDNS": "GARDENS",
}


def _normalise_address(address: str) -> str:
    tokens = address.upper().replace(",", " ").split()
    return " ".join(STREET_TYPE_ABBREVIATIONS.get(t, t) for t in tokens)


def _reduced_queries(address: str) -> list[str]:
    """Progressively shorter search terms for a strict address lookup.

    The address lookup returns nothing for spelled-out street types or
    appended suburbs, but happily lists candidates for "23 Bakana" — which
    then feed the suggestions flow.
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


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def _match_address(self, address: str) -> bool:
        return _normalise_address(self._address) == _normalise_address(address)

    def _search(self, session: requests.Session, address: str) -> list[dict]:
        r = session.post(ADDRESS_URL, json={"address": address}, timeout=30)
        r.raise_for_status()
        result = r.json()
        if not isinstance(result, list):
            return []
        return [item for item in result if isinstance(item, dict)]

    def _fetch_map_id(self, session: requests.Session) -> str:
        result = self._search(session, " ".join(self._address.split()))
        if not result:
            # The address lookup is strict: spelled-out street types,
            # commas or an appended suburb return nothing. Retry with a
            # shortened query ("23 Bakana"); the candidates it returns
            # either match after normalisation or become suggestions.
            for reduced in _reduced_queries(self._address):
                result = self._search(session, reduced)
                if result:
                    break
        if not result:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "please check the spelling and enter the address as the City of Wanneroo bin day lookup shows it, e.g. '1 Atlanta DR TWO ROCKS'.",
            )

        addresses = [str(item["address"]) for item in result if item.get("address")]
        matches = [
            item
            for item in result
            if item.get("mapId") and self._match_address(str(item.get("address")))
        ]
        # The same address can be listed more than once with the same mapId.
        map_ids = list(dict.fromkeys(str(item["mapId"]) for item in matches))
        if len(map_ids) == 1:
            return map_ids[0]
        if len(map_ids) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address", self._address, [str(item["address"]) for item in matches]
            )
        raise SourceArgumentNotFoundWithSuggestions("address", self._address, addresses)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        map_id = self._fetch_map_id(session)

        r = session.post(BINDAY_URL, json={"mapId": map_id}, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise Exception("Invalid response from the bin day lookup")

        entries = []
        for key, bin_type in BINS.items():
            item = data.get(key)
            if not isinstance(item, dict) or not item.get("collectDate"):
                continue
            try:
                date_ = datetime.fromisoformat(str(item["collectDate"])).date()
            except ValueError:
                continue
            entries.append(
                Collection(date=date_, t=bin_type, icon=ICON_MAP.get(bin_type))
            )

        if not entries:
            raise Exception(f"No collection dates found for address: {self._address}")

        return entries
