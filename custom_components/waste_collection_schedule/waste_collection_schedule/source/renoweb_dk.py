"""Support for Renoweb waste collection schedule."""

import json
import logging
import re
from datetime import datetime
from typing import List

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
)

TITLE = "RenoWeb"
DESCRIPTION = "RenoWeb collections"
URL = "https://renoweb.dk"
API_URL = "https://{municipality}.renoweb.dk/Legacy/JService.asmx/{{endpoint}}"

TEST_CASES = {
    "test_01": {
        "municipality": "frederiksberg",
        "address": "Roskildevej 40",
    },
    "test_02": {
        "municipality": "htk",
        "address_id": 45149,
    },
    "test_03": {
        "municipality": "rudersdal",
        "address": "Stationsvej 38",
    },
    "test_04": {
        "municipality": "fh",
        "address": "Odinsvej 58",
        "include_ordered_pickup_entries": True,
    },
}

_LOGGER = logging.getLogger("waste_collection_schedule.renoweb_dk")


class Source:
    """Source class for RenoWeb."""

    _api_url: str
    __address_id: int

    def __init__(
        self,
        municipality: str,
        address: str | None = None,
        address_id: int | None = None,
        include_ordered_pickup_entries: bool = False,
    ):
        _LOGGER.debug(
            "Source.__init__(); municipality=%s, address_id=%s, address=%s, include_ordered_pickup_entries=%s",
            municipality,
            address_id,
            address,
            include_ordered_pickup_entries,
        )

        self._api_url = API_URL.format(municipality=municipality.lower())
        self._include_ordered_pickup_entries = include_ordered_pickup_entries

        if address_id:
            self.__address_id = address_id

        elif address:
            self._address = address

        else:
            raise SourceArgumentExceptionMultiple(
                ("address", "address_id"),
                "Either address or address_id must be provided",
            )

        self._session = requests.Session()
        self._session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
            + "Gecko/20100101 Firefox/115.0",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

    def _get_address_id(self) -> None:
        """Get the address id."""
        response = self._session.post(
            url=self._api_url.format(endpoint="Adresse_SearchByString"),
            json={"searchterm": f"{self._address},", "addresswithmateriel": 3},
        )

        response.raise_for_status()

        _LOGGER.debug(
            "Address '%s'; id %s",
            json.loads(response.json()["d"])["list"][0]["label"],
            json.loads(response.json()["d"])["list"][0]["value"],
        )

        self.__address_id = json.loads(response.json()["d"])["list"][0]["value"]

    @property
    def _address_id(self) -> int:
        """Return the address id."""
        if not hasattr(self, f"_{self.__class__.__name__}__address_id"):
            self._get_address_id()

        return self.__address_id

    def fetch(self) -> List[Collection]:
        """Fetch data from RenoWeb."""
        _LOGGER.debug("Source.fetch()")

        entries: list[Collection] = []

        response = self._session.post(
            url=self._api_url.format(endpoint="GetAffaldsplanMateriel_mitAffald"),
            json={"adrid": self._address_id, "common": False},
        )

        response.raise_for_status()

        # For some reason the response is a JSON structure inside a JSON string
        data = json.loads(response.json()["d"])

        # If the response JSON contains nested "status" keys, we're probably
        # dealing with an error.
        status = data.get("status", None)
        if status:
            statusCode = status.get("status", None)
            statusMessage = status.get("msg", None)

            if statusCode in ["AccessDenied"]:
                _LOGGER.error("Source.fetch(): access denied; data=%s", data)
                raise ValueError(f"Access denied: {statusMessage}")
            elif statusCode:
                _LOGGER.error("Source.fetch(): unknown error; data=%s", data)
                raise ValueError(f'Unhandled error "{statusCode}": {statusMessage}')

        _LOGGER.debug(
            "Source.fetch(); response=%s, data=%s, address_id=%s",
            response,
            data,
            self._address_id,
        )

        waste_schemes = data["list"]

        if not waste_schemes:
            raise ValueError("No waste schemes found, check address or address_id")

        for entry in waste_schemes:
            include_entry = (
                self._include_ordered_pickup_entries
                or not entry["afhentningsbestillingmateriel"]
            )
            if include_entry and re.search(
                r"dag den \d{2}-\d{2}-\d{4}", entry["toemningsdato"]
            ):
                response = self._session.post(
                    url=self._api_url.format(endpoint="GetCalender_mitAffald"),
                    json={"materialid": entry["id"]},
                )

                response.raise_for_status()

                entry["name"] = " - ".join(
                    [entry["ordningnavn"], entry["materielnavn"]]
                )

                for date in [
                    datetime.strptime(date_string.split()[-1], "%d-%m-%Y").date()
                    for date_string in json.loads(response.json()["d"])["list"]
                ]:
                    entries.append(Collection(date=date, t=entry["name"]))

        return entries
