from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Gore, Invercargill & Southland"
DESCRIPTION = "Source for Wastenet.org.nz."
URL = "https://www.wastenet.org.nz"
TEST_CASES = {
    "166 Lewis Street, Invercargill": {"address": "166 Lewis Street, Invercargill"},
    "Old Format: 199 Crawford Street INVERCARGILL": {
        "address": "199 Crawford Street INVERCARGILL"
    },
    "Old Format: 156 Tay Street INVERCARGILL": {
        "address": "156 Tay Street INVERCARGILL"
    },
    "Gore: 1 Anderson Place": {"address": "1 Anderson Place, Gore"},
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.wastenet.org.nz/3-bin-day-finder",
}

ADDRESS_LIST_URL = "https://www.wastenet.org.nz/client-api/icc/rubbish/address-list"
SEARCH_URL = "https://www.wastenet.org.nz/client-api/icc/rubbish/search"

# Council identifier returned by the API
COUNCIL_ICC = 1  # Invercargill City Council


class Source:
    def __init__(self, address: str):
        # Normalise old-style "STREET INVERCARGILL" format to "STREET, Invercargill"
        self._address = address.replace(" INVERCARGILL", ", Invercargill").strip()

    def _resolve_address(self, session: requests.Session) -> str:
        """Look up the canonical address from the provider's address list."""
        r = session.get(ADDRESS_LIST_URL)
        r.raise_for_status()
        candidates: list[dict] = r.json()

        # Exact match (case-insensitive)
        for candidate in candidates:
            if candidate["address"].lower() == self._address.lower():
                return candidate["address"]

        # Partial match: find entries that contain the search string
        partial = [
            c["address"]
            for c in candidates
            if self._address.lower() in c["address"].lower()
        ]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, partial[:10]
            )

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            [c["address"] for c in candidates[:5]],
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        canonical_address = self._resolve_address(session)

        r = session.get(SEARCH_URL, params={"address": canonical_address})
        r.raise_for_status()

        data = r.json()
        council: int = data.get("Council", COUNCIL_ICC)
        entries: list[Collection] = []

        for item in data.get("NextDates", []):
            date = datetime.fromisoformat(item["Date"]).date()
            week = item["Week"]  # "Red Week" or "Yellow Week"

            if week == "Red Week":
                entries.append(
                    Collection(date, "General Waste", ICON_MAP["General Waste"])
                )
            elif week == "Yellow Week":
                if council == COUNCIL_ICC:
                    entries.append(
                        Collection(date, "General Waste", ICON_MAP["General Waste"])
                    )
                entries.append(Collection(date, "Recycling", ICON_MAP["Recycling"]))

        return entries
