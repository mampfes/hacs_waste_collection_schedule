import datetime
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Avfall Sør, Kristiansand"
DESCRIPTION = "Source for Avfall Sør, Kristiansand."
URL = "https://avfallsor.no/"
TEST_CASES = {"Auglandslia 1, Kristiansand": {"address": "Auglandslia 1, Kristiansand"}}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Bioavfall": "mdi:leaf",
    "Papp og papir": "mdi:package-variant",
    "Plastemballasje": "mdi:recycle",
    "Glass- og metallemballasje": "mdi:bottle-soda",
    "residual": "mdi:trash-can",
    "bio": "mdi:leaf",
    "paper": "mdi:package-variant",
    "plastic": "mdi:recycle",
    "glass": "mdi:bottle-soda",
    "metal": "mdi:bottle-soda",
}


API_URL = "https://avfallsor.no/wp-json/addresses/v1/address"


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def fetch(self) -> list[Collection]:
        args = {"lookup_term": self._address.split(",")[0].strip()}

        r = requests.get(API_URL, params=args)
        r.raise_for_status()
        matches = r.json()
        href: str | None = None

        for match in matches:
            if (
                match["label"]
                .lower()
                .replace(" ", "")
                .replace(",", "")
                .replace(".", "")
                .casefold()
                == self._address.lower()
                .replace(" ", "")
                .replace(",", "")
                .replace(".", "")
                .casefold()
            ):
                href = match["href"]
                break

        if not href:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [match["label"] for match in matches],
            )

        # Extract propertyId from href
        match = re.search(r'/([0-9a-f-]{36})/?$', href)
        if not match:
            raise ValueError(f"Could not extract propertyId from href: {href}")
        property_id = match.group(1)

        api_url = f"https://avfallsor.no/wp-json/pickup-calendar/v1/collections/property-id/{property_id}"
        r = requests.get(api_url)
        r.raise_for_status()
        data = r.json()

        entries = []
        today = datetime.date.today()
        for collection in data.get("collections", []):
            date_str = collection.get("dateIndex")
            if not date_str:
                continue
            try:
                date = datetime.date.fromisoformat(date_str)
            except ValueError:
                continue
            if date < today:
                continue
            waste_types = []
            for item in collection.get("items", []):
                waste_types.extend(item.get("wasteIcons", []))
            for waste_type in waste_types:
                icon = ICON_MAP.get(waste_type)
                entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
