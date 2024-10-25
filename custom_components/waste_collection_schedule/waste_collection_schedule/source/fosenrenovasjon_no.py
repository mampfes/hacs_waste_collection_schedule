from datetime import datetime
from urllib.parse import quote

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Fosen Renovasjon"
DESCRIPTION = "Source for Fosen Renovasjon."
URL = "https://fosenrenovasjon.no/"
TEST_CASES = {"Lysøysundveien 117": {"address": "Lysøysundveien 117"}}


ICON_MAP = {
    "Restavfall til forbrenning": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Papir og plastemballasje": "mdi:recycle",
}


ADDRESS_URL = "https://fosen.renovasjonsportal.no/api/address/{address}"
COLLECTIONS_URL = ADDRESS_URL + "/details"


class Source:
    def __init__(self, address: str):
        self._address = address.lower().strip()
        self._address_id: str | None = None

    def _fetch_address_id(self):
        url = ADDRESS_URL.format(address=quote(self._address))
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if not data:
            raise SourceArgumentNotFound()
        for address in data["searchResults"]:
            if address["title"].lower().strip() == self._address:
                self._address_id = address["id"]
                return

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            [address["title"] for address in data["searchResults"]],
        )

    def fetch(self) -> list[Collection]:
        new_id = False
        if self._address_id is None:
            new_id = False
            self._fetch_address_id()
        try:
            return self._get_collections()
        except Exception:
            if new_id:
                raise
            self._fetch_address_id()
            return self._get_collections()

    def _get_collections(self) -> list[Collection]:
        if self._address_id is None:
            raise ValueError("Address not found", self._address)
        url = COLLECTIONS_URL.format(address=self._address_id)
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        entries: list[Collection] = []
        for d in data["disposals"]:
            date = datetime.strptime(d["date"], "%Y-%m-%dT%H:%M:%S").date()
            entries.append(
                Collection(date=date, t=d["fraction"], icon=ICON_MAP.get(d["fraction"]))
            )

        return entries
