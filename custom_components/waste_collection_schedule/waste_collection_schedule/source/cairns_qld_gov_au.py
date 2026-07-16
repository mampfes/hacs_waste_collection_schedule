import json
import re
from datetime import date, timedelta

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Cairns Regional Council"
DESCRIPTION = "Source for Cairns Regional Council, QLD, Australia."
URL = "https://www.cairns.qld.gov.au"
TEST_CASES = {
    "7 Keats Close, Mount Sheridan": {"address": "7 Keats Close, MOUNT SHERIDAN"},
    "1 Abington Close, Redlynch": {"address": "1 Abington Close, Redlynch"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to the Cairns Regional Council 'Find my bin day' page "
    "(https://www.cairns.qld.gov.au/water-waste-roads/waste-and-recycling/bin-collection/find-bin-day), "
    "start typing your address and pick it from the autocomplete list. Use the same "
    "'STREET NUMBER STREET NAME, SUBURB' format shown in the suggestion for the `address` argument.",
    "de": "Rufe die Seite 'Find my bin day' des Cairns Regional Council auf "
    "(https://www.cairns.qld.gov.au/water-waste-roads/waste-and-recycling/bin-collection/find-bin-day), "
    "gib deine Adresse ein und wähle sie aus der Autovervollständigung aus. Verwende für das Argument "
    "`address` das gleiche Format 'HAUSNUMMER STRASSE, VORORT' wie im Vorschlag angezeigt.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address, e.g. '7 Keats Close, MOUNT SHERIDAN' "
        "(exactly as shown in the website's address autocomplete)."
    },
    "de": {
        "address": "Vollständige Adresse, z. B. '7 Keats Close, MOUNT SHERIDAN' "
        "(genau wie in der Autovervollständigung der Webseite angezeigt)."
    },
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
    "de": {"address": "Adresse"},
}

ADDRESS_SEARCH_URL = (
    "https://www.cairns.qld.gov.au/_external/my-property/address-search"
)
PROPERTY_SEARCH_URL = (
    "https://www.cairns.qld.gov.au/property-and-business/property-search"
)

_PROPERTY_DATA_RE = re.compile(r"var PropertyData = (\{.*?\});", re.DOTALL)

_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

# Number of future occurrences to generate for each waste type.
_WASTE_WEEKS_AHEAD = 52
_RECYCLE_FORTNIGHTS_AHEAD = 26


def _parse_next_recycle_date(text: str, today: date) -> date:
    # Expected format: "Thu 23 July" (no year supplied by the API).
    parts = text.split()
    day = int(parts[-2])
    month = _MONTHS[parts[-1]]
    year = today.year
    result = date(year, month, day)
    if result < today:
        result = date(year + 1, month, day)
    return result


class Source:
    def __init__(self, address: str):
        self._address = address

    def _find_address_id(self, session: "requests.Session") -> str:
        r = session.get(ADDRESS_SEARCH_URL, params={"search": self._address})
        r.raise_for_status()
        results = r.json()

        if not results:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        normalized_input = re.sub(r"\s+", " ", self._address).strip().lower()
        normalized_input = normalized_input.rstrip(",")

        formatted = [f"{item['streetAddress']}, {item['suburb']}" for item in results]

        for item, label in zip(results, formatted, strict=False):
            normalized_label = re.sub(r"\s+", " ", label).strip().lower()
            if normalized_label == normalized_input:
                return str(item["addressId"])

        if len(results) == 1:
            return str(results[0]["addressId"])

        raise SourceArgumentNotFoundWithSuggestions(
            "address", self._address, formatted[:15]
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        address_id = self._find_address_id(session)

        r = session.get(PROPERTY_SEARCH_URL, params={"address-id": address_id})
        r.raise_for_status()

        match = _PROPERTY_DATA_RE.search(r.text)
        if not match:
            raise ValueError(
                "Could not find property data on the Cairns Regional Council "
                "website. The page layout may have changed."
            )

        property_data = json.loads(match.group(1))
        bin_data = property_data.get("binData")
        if not bin_data:
            raise ValueError(
                f"No bin collection data found for address '{self._address}'."
            )

        today = date.today()

        entries: list[Collection] = []

        waste_date_iso = bin_data.get("runDateWaste")
        if waste_date_iso:
            waste_date = date.fromisoformat(waste_date_iso.split("T")[0])
            d = waste_date
            for _ in range(_WASTE_WEEKS_AHEAD):
                entries.append(
                    Collection(d, "General Waste", ICON_MAP["General Waste"])
                )
                d += timedelta(weeks=1)

        recycle_date_text = bin_data.get("runDateRecycle")
        if recycle_date_text:
            d = _parse_next_recycle_date(recycle_date_text, today)
            for _ in range(_RECYCLE_FORTNIGHTS_AHEAD):
                entries.append(Collection(d, "Recycling", ICON_MAP["Recycling"]))
                d += timedelta(weeks=2)

        return entries
