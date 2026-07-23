import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "GLØR"
DESCRIPTION = (
    "Source for GLØR (Gudbrandsdal Lillehammer Øyer Ringebu Renovasjon), Norway."
)
URL = "https://glor.no"
COUNTRY = "no"

TEST_CASES = {
    "Storgata 1, Lillehammer": {"address": "Storgata 1, Lillehammer"},
    "Segalstadsetervegen 33, Gausdal": {"address": "Segalstadsetervegen 33, Gausdal"},
    "Gudbrandsdalsvegen 187 (without city)": {"address": "Gudbrandsdalsvegen 187"},
}

SEARCH_URL = "https://proaktiv.glor.offcenit.no/search"
DETAILS_URL = "https://proaktiv.glor.offcenit.no/details"
REQUEST_TIMEOUT = 30

ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Papir, papp": Icons.PAPER,
    "Plast blandet": Icons.PLASTIC_PACKAGING,
    "Matavfall": Icons.BIO_KITCHEN,
    "Hermetikk- og glassemballasje": Icons.GLASS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your address at glor.no/tømmeplan. Use the address exactly "
        "as shown in the result list, optionally followed by the municipality "
        "name, for example 'Storgata 1, Lillehammer'."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address, optionally followed by the municipality, e.g. 'Storgata 1, Lillehammer'.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    }
}


def _normalize(value: str) -> str:
    return "".join(value.casefold().replace(".", "").replace(",", "").split())


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        candidates = self._lookup_properties()

        entries: list[Collection] = []
        seen: set[tuple[str, str]] = set()
        for candidate in candidates:
            r = requests.get(
                DETAILS_URL,
                params={"id": candidate["id"]},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            for item in r.json():
                date_str = item["dato"][:10]
                waste_type = item["fraksjon"]
                key = (date_str, waste_type)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(
                        date=datetime.date.fromisoformat(date_str),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        if not entries:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "no collection schedule found for this address",
            )

        return entries

    def _lookup_properties(self) -> list[dict]:
        # The municipality name may optionally be appended after a comma, e.g.
        # "Storgata 1, Lillehammer". The search API only matches on the
        # street + house number part, so that is what is used as the query.
        address_part = self._address.split(",")[0].strip()
        kommune_part = (
            self._address.split(",", 1)[1].strip() if "," in self._address else None
        )

        r = requests.get(
            SEARCH_URL, params={"q": address_part}, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        matches = r.json()

        addr_norm = _normalize(address_part)
        candidates = [m for m in matches if _normalize(m["adresse"]) == addr_norm]

        if kommune_part:
            kommune_norm = _normalize(kommune_part)
            candidates = [
                m for m in candidates if _normalize(m["kommune"]) == kommune_norm
            ]
        elif len({m["kommune"] for m in candidates}) > 1:
            # The same street name exists in more than one municipality served
            # by GLØR — the user needs to disambiguate by adding the
            # municipality name after a comma.
            suggestions = sorted(
                {f"{m['adresse']}, {m['kommune']}" for m in candidates}
            )
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions
            )

        if not candidates:
            suggestions = sorted({f"{m['adresse']}, {m['kommune']}" for m in matches})
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions
            )

        return candidates
