import datetime
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Avfall Sør, Kristiansand"
DESCRIPTION = "Source for Avfall Sør, Kristiansand."
URL = "https://avfallsor.no/"
TEST_CASES = {"Auglandslia 1, Kristiansand": {"address": "Auglandslia 1, Kristiansand"}}

# Maps fraksjonId to English waste type names
# fraksjonId is the stable provider identifier
FRAKSJON_ID_MAP = {
    "9011": "Residual",  # Restavfall
    "1111": "Bio",  # Bioavfall
    "2499": {
        # This fraksjonId maps to multiple waste types depending on fraksjon field
        "Papp og papir": "Paper",
        "Plastemballasje": "Plastic",
    },
    "1322": {
        # This fraksjonId contains multiple waste types
        "Glass- og metallemballasje": ["Glass", "Metal"],
    },
}

ICON_MAP = {
    "Residual": "mdi:trash-can",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Plastic": "mdi:recycle",
    "Glass": "mdi:bottle-soda",
    "Metal": "mdi:bottle-soda",
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
            for item in collection.get("items", []):
                fraksjon_id = item.get("fraksjonId")
                fraksjon = item.get("fraksjon")
                
                # Look up English waste type name using fraksjonId
                mapping = FRAKSJON_ID_MAP.get(fraksjon_id)
                
                # Handle nested mappings for fraksjonIds with multiple waste types
                if isinstance(mapping, dict):
                    # Lookup by both fraksjonId and fraksjon name
                    waste_type_value = mapping.get(fraksjon)
                    if isinstance(waste_type_value, list):
                        waste_types = waste_type_value
                    else:
                        waste_types = [waste_type_value] if waste_type_value else []
                else:
                    # Single waste type for this fraksjonId
                    waste_types = [mapping] if mapping else []
                
                # Create collection entries for each waste type
                for waste_type in waste_types:
                    if waste_type:
                        icon = ICON_MAP.get(waste_type)
                        entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
