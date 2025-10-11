from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, date
from typing import Iterable

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Komunala Kranj"
DESCRIPTION = "Source for Komunala Kranj."
URL = "https://www.komunala-kranj.si/"
TEST_CASES = {
    "Rakovica": {"address": "Rakovica 31, Rakovica"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the street name and house number exactly as shown in the Komunala Kranj address search.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address as accepted by the Komunala Kranj address search (e.g. 'Street 1, City').",
    }
}


ADDRESS_URL = "https://gis.komunala-kranj.si/mapguide/KaliopaFDOService/Service.asmx/GetResultsSimplified"
SCHEDULE_URL = "https://gis.komunala-kranj.si/ddmoduli/EkoloskiOtoki.asmx/GetKoledarOdvozov"
API_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
}
DEFAULT_DAYS_AHEAD = 60


@dataclass(frozen=True)
class _AddressMatch:
    identifier: str
    description: str


def _parse_date(value: str | date | datetime) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    if text.startswith("/Date(") and text.endswith(")/"):
        timestamp_text = text[len("/Date(") : -len(")/")]
        # remove optional timezone information (e.g. +0200) if present
        if "+" in timestamp_text or "-" in timestamp_text[1:]:
            for sep in ("+", "-"):
                if sep in timestamp_text[1:]:
                    timestamp_text = timestamp_text.split(sep, 1)[0]
                    break
        timestamp = int(timestamp_text)
        return datetime.fromtimestamp(timestamp / 1000, tz=UTC).date()
    raise ValueError(f"Cannot parse date from value: {value!r}")


def _suggestions(matches: Iterable[_AddressMatch]) -> list[str]:
    return sorted({match.description for match in matches if match.description})


def _guess_icon(text: str) -> str | None:
    lowered = text.lower()
    if "bio" in lowered:
        return "mdi:leaf"
    if "embala" in lowered or "plasti" in lowered:
        return "mdi:recycle"
    if "stek" in lowered:
        return "mdi:glass-fragile"
    if "papir" in lowered:
        return "mdi:newspaper"
    if "kosov" in lowered:
        return "mdi:sofa"
    if "mešan" in lowered or "mesan" in lowered:
        return "mdi:trash-can"
    return None


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        match = self._get_address_match()

        schedule_params = {
            "a": "komunalakranj",
            "hsMid": match.identifier,
            "stDni": str(DEFAULT_DAYS_AHEAD),
        }
        response = requests.get(
            SCHEDULE_URL, params=schedule_params, headers=API_HEADERS, timeout=30
        )
        response.raise_for_status()

        entries: list[Collection] = []
        for item in response.json().get("d", []):
            raw_date = (
                item.get("Datum")
                or item.get("DatumSort")
                or item.get("DatumSorten")
                or item.get("DatumSortEn")
            )
            if not raw_date:
                continue
            collection_date = _parse_date(raw_date)

            waste_type = str(item.get("VrstaOdpadka") or "").strip()
            container_type = str(item.get("VrstaZabojnika") or "").strip()

            if waste_type and container_type and container_type not in waste_type:
                type_name = f"{waste_type} ({container_type})"
            else:
                type_name = waste_type or container_type or "Waste Collection"

            icon = _guess_icon(waste_type or container_type)
            entries.append(Collection(date=collection_date, t=type_name, icon=icon))

        return entries

    def _get_address_match(self) -> _AddressMatch:
        params = {
            "a": "hisnestevilkekranj",
            "mapName": "map",
            "locale": "SI",
            "query": self._address,
        }
        response = requests.get(
            ADDRESS_URL, params=params, headers=API_HEADERS, timeout=30
        )
        response.raise_for_status()

        matches = [
            _AddressMatch(identifier=str(item.get("Id", "")), description=str(item.get("Text", "")))
            for item in response.json().get("d", [])
        ]

        matches = [m for m in matches if m.identifier]
        if not matches:
            raise SourceArgumentNotFound("address", self._address)

        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address", self._address, _suggestions(matches)
            )

        return matches[0]
