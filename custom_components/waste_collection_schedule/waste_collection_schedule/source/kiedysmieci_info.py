import datetime
from typing import Any

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Kiedy śmieci"
DESCRIPTION = "Source script for Kiedy śmieci, Poland"
URL = "https://kiedysmieci.info"
COUNTRY = "pl"
TEST_CASES = {
    "Nadolany, podkarpackie, sanocki, Bukowsko": {
        "voivodeship": "podkarpackie",
        "district": "sanocki",
        "municipality": "Bukowsko",
        "street": "Nadolany",
    },
    "Kędzierz, podkarpackie, dębicki, Dębica": {
        "voivodeship": "podkarpackie",
        "district": "dębicki",
        "municipality": "Dębica",
        "street": "Kędzierz",
    },
    "Parkowa, lubelskie, zamojski, Szczebrzeszyn": {
        "voivodeship": "lubelskie",
        "district": "zamojski",
        "municipality": "Szczebrzeszyn",
        "street": "Parkowa",
    },
}

API_URL = "https://kiedysmieci.info/schedule-proxy.php"

ICON_MAP = {
    "zmieszane": Icons.GENERAL_WASTE,
    "metale i tworzywa sztuczne": Icons.METAL,
    "papier i tektura": Icons.PAPER,
    "szkło": Icons.GLASS,
    "biodegradowalne": Icons.BIO_KITCHEN,
}

# The location cascade, from the widest to the narrowest level:
# source argument -> query parameter (which doubles as the key of a returned
# item) -> key holding the list of options in the response.
LOCATION_LEVELS = (
    ("voivodeship", "wojewodztwo", "listaWojewodztw"),
    ("district", "powiat", "listaPowiatow"),
    ("municipality", "gmina", "listaGmin"),
    ("street", "ulica", "listaUlic"),
)

# A known location without a published schedule yields a single placeholder
# entry instead of an empty list.
NO_SCHEDULE_MARKER = "brak harmonogramu"


class Source:
    def __init__(self, voivodeship: str, district: str, municipality: str, street: str):
        self._location = {
            "wojewodztwo": voivodeship,
            "powiat": district,
            "gmina": municipality,
            "ulica": street,
        }

    def _get(self, request_type: str, params: dict[str, str]) -> dict[str, Any]:
        response = requests.get(
            API_URL, params={"type": request_type} | params, timeout=30
        )

        # Errors are reported in the JSON envelope (with a 4xx/5xx status), so
        # parse the body before looking at the status code.
        try:
            payload = response.json()
        except ValueError:
            response.raise_for_status()
            raise

        if not payload.get("ok"):
            raise Exception(
                payload.get("message") or "Unexpected response from kiedysmieci.info"
            )

        return payload.get("data") or {}

    def _validate_location(self) -> None:
        """Walk the location cascade and report the first argument that is unknown.

        Returns without raising if every level matches, which means the request
        failed for another reason.
        """
        selection: dict[str, str] = {}

        for argument, param, list_key in LOCATION_LEVELS:
            try:
                items = self._get("locations", selection).get(list_key) or []
            except Exception:
                # The cascade itself is unreachable, so it cannot tell us
                # anything - leave the original error to the caller.
                return

            options = [item[param] for item in items if item.get(param)]
            value = self._location[param]
            match = next((o for o in options if o.lower() == value.lower()), None)

            if match is None:
                raise SourceArgumentNotFoundWithSuggestions(argument, value, options)

            selection[param] = match

    def fetch(self) -> list[Collection]:
        try:
            data = self._get("terms", self._location)
        except Exception:
            # Turn a generic "not found" from the API into an error pointing at
            # the argument that is actually wrong.
            self._validate_location()
            raise

        schedule = data.get("listaTerminow") or []
        entries = [
            Collection(
                date=datetime.datetime.strptime(
                    entry["dataOdbioru"], "%Y-%m-%d"
                ).date(),
                t=entry["nazwaTypuSmieci"],
                icon=ICON_MAP.get(entry["nazwaTypuSmieci"], Icons.GENERAL_WASTE),
            )
            for entry in schedule
            if entry.get("dzienTygodnia") != NO_SCHEDULE_MARKER
        ]

        if not entries:
            self._validate_location()
            raise SourceArgumentExceptionMultiple(
                ("municipality", "street"),
                f"No schedule published for {self._location['ulica']}, "
                f"{self._location['gmina']}",
            )

        return entries
