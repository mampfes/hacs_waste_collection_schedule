"""Support for Renoweb waste collection schedule."""

import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "RenoWeb"
DESCRIPTION = "RenoWeb collections"
URL = "https://renoweb.dk"
COUNTRY = "dk"

API_URL = "https://servicesgh.renoweb.dk/v1_13/{endpoint}"

# Public application key used by RenoWeb's own "Mit Affald" app. This grants the
# same anonymous, read-only access the app itself uses; it is not a per-user
# credential and does not require a MitID login. Identified via briis/affalddk
# (MIT-licensed, https://github.com/briis/affalddk), which uses the same key.
API_KEY = "479D40F4-B3E1-4038-9130-76453188C74C"

# RenoWeb's old "Legacy/JService.asmx" API (used by this source until mid-2025)
# now requires a MitID login and can no longer be used
# (see https://github.com/mampfes/hacs_waste_collection_schedule/issues/4084).
# A number of municipalities that used to run on RenoWeb have also since moved
# their backend entirely to a different vendor (mostly "Perfect Waste"), which
# is not supported by this source.
#
# MUNICIPALITY_CODES only lists the municipalities that are (as of September
# 2026) still served by RenoWeb's public "servicesgh" API, keyed by the
# official Danish municipality ("kommune") code.
MUNICIPALITY_CODES = {
    "aabenraa": "0580",
    "aalborg": "0851",
    "billund": "0530",
    "bornholm": "0400",
    "brondby": "0153",
    "bronderslev": "0810",
    "dragoer": "0155",
    "egedal": "0240",
    "esbjerg": "0561",
    "fredensborg": "0210",
    "gentofte": "0157",
    "glostrup": "0161",
    "hjorring": "0860",
    "jammerbugt": "0849",
    "kerteminde": "0440",
    "mariagerfjord": "0846",
    "randers": "0730",
    "rodovre": "0175",
    "samsoe": "0741",
    "svendborg": "0479",
    "sonderborg": "0540",
    "varde": "0573",
    "vordingborg": "0390",
}

TEST_CASES = {
    "Esbjerg": {
        "municipality": "Esbjerg",
        "address": "Torvegade 3, 6700 Esbjerg",
    },
    "Aalborg": {
        "municipality": "Aalborg",
        "address": "Hasserisvej 97",
    },
    "Rødovre": {
        "municipality": "Rødovre",
        "address": "Rødovre Parkvej 150",
    },
}

_LOGGER = logging.getLogger("waste_collection_schedule.renoweb_dk")

ADDRESS_PATTERN = re.compile(
    r"^\s*(?P<street>.+?)\s+(?P<house_number>\d+)\s*(?P<letter>[A-Za-z]?)"
    r"\s*(?:,\s*(?P<zipcode>\d{4})\b.*)?\s*$"
)

DANISH_TRANSLITERATION = str.maketrans({"æ": "ae", "ø": "o", "å": "aa"})


def _normalize_municipality(municipality: str) -> str:
    return municipality.strip().lower().translate(DANISH_TRANSLITERATION)


class Source:
    """Source class for RenoWeb."""

    def __init__(self, municipality: str, address: str):
        _LOGGER.debug(
            "Source.__init__(); municipality=%s, address=%s", municipality, address
        )

        key = _normalize_municipality(municipality)
        if key not in MUNICIPALITY_CODES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality",
                municipality,
                sorted(MUNICIPALITY_CODES.keys()),
            )
        self._municipality_code = MUNICIPALITY_CODES[key]

        match = ADDRESS_PATTERN.match(address)
        if not match:
            raise SourceArgumentException(
                "address",
                f"Could not parse address '{address}', "
                "expected e.g. 'Torvegade 3, 6700 Esbjerg' or 'Torvegade 3'",
            )

        self._street = match.group("street").strip()
        self._house_number = match.group("house_number").strip()
        self._letter = (match.group("letter") or "").strip()
        self._zipcode = match.group("zipcode")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
                "Gecko/20100101 Firefox/115.0",
                "Accept-Encoding": "gzip",
            }
        )

    def _get(self, endpoint: str, **params) -> dict:
        params["apikey"] = API_KEY
        params["municipalitycode"] = self._municipality_code
        response = self._session.get(API_URL.format(endpoint=endpoint), params=params)
        response.raise_for_status()
        return response.json()

    def _get_road_id(self) -> int:
        data = self._get("GetJSONRoad.aspx", roadname=self._street)
        roads = data.get("list") or []

        if self._zipcode:
            roads = [r for r in roads if f"({self._zipcode})" in r.get("name", "")]

        if not roads:
            raise SourceArgumentNotFoundWithSuggestions("address", self._street, [])

        if len(roads) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self._street,
                [r["name"] for r in roads],
            )

        return roads[0]["id"]

    def _get_address_id(self) -> int:
        road_id = self._get_road_id()
        data = self._get(
            "GetJSONAdress.aspx",
            roadid=road_id,
            streetBuildingIdentifier=self._house_number,
        )
        addresses = data.get("list") or []

        # Prefer the main entrance (no floor/suite) matching the given letter
        # (or no letter at all), so a plain "<street> <number>" address doesn't
        # become ambiguous just because the building also has flats.
        main_addresses = [
            a
            for a in addresses
            if not a.get("floor")
            and not a.get("suite")
            and str(a.get("letter", "")).lower() == self._letter.lower()
        ]
        if main_addresses:
            addresses = main_addresses

        if not addresses:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                f"{self._street} {self._house_number}{self._letter}",
                [],
            )

        if len(addresses) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                f"{self._street} {self._house_number}{self._letter}",
                [a["presentationString"] for a in addresses],
            )

        return addresses[0]["id"]

    def fetch(self) -> list[Collection]:
        """Fetch data from RenoWeb."""
        _LOGGER.debug("Source.fetch()")

        address_id = self._get_address_id()

        data = self._get(
            "GetJSONContainerList.aspx",
            adressId=address_id,
            fullinfo=1,
            supportsSharedEquipment=0,
        )

        entries: list[Collection] = []
        for entry in data.get("list") or []:
            timestamp = entry.get("nextpickupdatetimestamp")
            if not timestamp:
                # No regular collection scheduled for this container (e.g. an
                # order-only service), skip it.
                continue

            date = datetime.fromtimestamp(int(timestamp)).date()
            waste_type = entry.get("module", {}).get("fractionname") or entry["name"]
            entries.append(Collection(date=date, t=waste_type))

        if not entries:
            raise SourceArgumentException(
                "address", "No waste schemes found, check address"
            )

        return entries
