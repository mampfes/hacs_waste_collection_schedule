import datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Renovasjonsselskapet for Drammensregionen IKS (RfD)"
DESCRIPTION = "Source for RfD waste collection schedules"
URL = "https://www.rfd.no"
COUNTRY = "no"

TEST_CASES = {
    "RfD office": {
        "address": "Grønland 1, Drammen",
    }
}

API_URL = "https://www.rfd.no/_/service/com.enonic.app.rfd"
DEFAULT_DAYS = 114
REQUEST_TIMEOUT = 30

FRACTION_MAP = {
    1: "Mat- og restavfall",
    2: "Papiravfall",
    4: "Glass- og metallemballasje",
    5: "Hageavfall",
    7: "Plastemballasje",
    11: "Mat- og restavfall",
}

ICON_MAP = {
    "Mat- og restavfall": Icons.GENERAL_WASTE,
    "Papiravfall": Icons.PAPER,
    "Glass- og metallemballasje": Icons.GLASS,
    "Hageavfall": Icons.GARDEN,
    "Plastemballasje": Icons.PLASTIC_PACKAGING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your address at rfd.no/avfallshenting. Use the address exactly "
        "as shown in the result list, for example 'Grønland 1, Drammen'."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address as shown in the RfD address search results.",
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
        address = self._lookup_address()
        args = {
            "address": address["Text"],
            "postCode": address["PostNummer"],
            "region_id": address["KommuneNummer"],
            "street_code": address["GateId"],
            "street": address["GateNavn"],
            "house_number": address["AdresseHusNummer"],
            "days": DEFAULT_DAYS,
        }
        if address.get("AdresseBokstav"):
            args["address_letter"] = address["AdresseBokstav"]

        response = requests.get(
            f"{API_URL}/pickupDays", params=args, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data.get("message"):
            raise SourceArgumentNotFound("address", data["message"])

        fetch_days = data.get("fetchDays", [])
        if not fetch_days:
            raise SourceArgumentNotFound("address", "No collection schedule found")

        entries = []
        for item in fetch_days:
            fraction_id = item.get("fraksjonId")
            waste_type = FRACTION_MAP.get(fraction_id)
            if waste_type is None:
                continue

            for date_value in item.get("tommedatoer", []):
                date = datetime.datetime.fromisoformat(date_value).date()
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        if not entries:
            raise SourceArgumentNotFound(
                "address", "No supported collection types found"
            )

        return entries

    def _lookup_address(self) -> dict:
        response = requests.get(
            f"{API_URL}/addressLookup",
            params={"address": self._address, "size": 10, "source": "pickup"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        addresses = response.json().get("addresses", [])

        if not addresses:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        if len(addresses) == 1:
            return addresses[0]

        address_normalized = _normalize(self._address)
        exact_matches = [
            address
            for address in addresses
            if _normalize(address.get("Text", "")) == address_normalized
        ]

        if len(exact_matches) == 1:
            return exact_matches[0]

        suggestions = [address["Text"] for address in addresses if address.get("Text")]
        if exact_matches:
            suggestions = [
                address["Text"] for address in exact_matches if address.get("Text")
            ]

        raise SourceArgAmbiguousWithSuggestions(
            "address",
            self._address,
            suggestions,
        )
