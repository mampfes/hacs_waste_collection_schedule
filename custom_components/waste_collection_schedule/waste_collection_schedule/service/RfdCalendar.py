"""RfdCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime
import re
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://www.rfd.no/_/service/com.enonic.app.rfd"
WEBSITE_URL = "https://www.rfd.no/avfallshenting"
SEARCH_URL = f"{WEBSITE_URL}/_/service/com.enonic.app.rfd/collectionDaySearch"
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
WEBSITE_FRACTION_MAP = {
    "Restavfall": "Restavfall",
    "Matavfall": "Matavfall",
    "Papiravfall": "Papiravfall",
    "Glass/metall": "Glass- og metallemballasje",
    "Hageavfall": "Hageavfall",
    "Plastemballasje": "Plastemballasje",
}
MONTHS = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def _normalize(value: str) -> str:
    return "".join(value.casefold().replace(".", "").replace(",", "").split())


def _house_number(value: str) -> tuple[str, str]:
    """Split '7', '14A', '39 A og B' or '9, Idrettshall' into number and letter."""
    match = re.match("\\s*(\\d+)\\s*([a-zæøå]?)(?![a-zæøå])", value.casefold())
    return (match.group(1), match.group(2)) if match else ("", "")


def _address_forms(address: dict) -> set[str]:
    """Return the normalized spellings accepted for an address result."""
    street = f"{address.get('GateNavn', '')} {address.get('AdresseHusNummer', '')}{address.get('AdresseBokstav') or ''}"
    forms = {address.get("Text", "")}
    for place in (
        address.get("KommuneNavn"),
        f"{address.get('PostNummer', '')} {address.get('PostSted', '')}",
    ):
        if place and street.strip():
            forms.add(f"{street}, {place}")
    return {_normalize(form) for form in forms if form}


class _CalendarClient:
    _session: Any

    def __init__(self, address: str):
        self._address = address

    def retrieve(self) -> Any:
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
        response = self._session.get(
            f"{API_URL}/pickupDays", params=args, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        if data.get("message"):
            raise SourceArgumentNotFound("address", self._address, data["message"])
        fetch_days = data.get("fetchDays", [])
        if not fetch_days:
            return "html", self._fetch_from_website(address)
        return "json", response

    def parse(self, raw):
        mode, response = raw
        if mode == "html":
            return self._parse_website(response)
        fetch_days = response.json().get("fetchDays", [])
        entries = []
        for item in fetch_days:
            fraction_id = item.get("fraksjonId")
            waste_type = FRACTION_MAP.get(fraction_id)
            if waste_type is None:
                continue
            for date_value in item.get("tommedatoer", []):
                date = datetime.datetime.fromisoformat(date_value).date()
                entries.append({"date": date, "type": waste_type})
        if not entries:
            raise SourceArgumentNotFound(
                "address", self._address, "No supported collection types found"
            )
        return entries

    def _lookup_address(self) -> dict:
        response = self._session.get(
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
            if address_normalized in _address_forms(address)
        ]
        if len(exact_matches) == 1:
            return exact_matches[0]
        suggestions = [address["Text"] for address in addresses if address.get("Text")]
        if exact_matches:
            suggestions = [
                address["Text"] for address in exact_matches if address.get("Text")
            ]
        raise SourceArgAmbiguousWithSuggestions("address", self._address, suggestions)

    def _fetch_from_website(self, address: dict) -> Any:
        number = str(address["AdresseHusNummer"])
        letter = (address.get("AdresseBokstav") or "").casefold()
        response = self._session.get(
            SEARCH_URL,
            params={"q": f"{address['GateNavn']} {number}{letter}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        suggestions = [
            suggestion
            for suggestion in response.json().get("suggestions", [])
            if suggestion.get("postalCode") == address["PostNummer"]
            and _normalize(suggestion.get("street", ""))
            == _normalize(address["GateNavn"])
            and (_house_number(suggestion.get("number", ""))[0] == number)
        ]
        exact = [
            suggestion
            for suggestion in suggestions
            if _house_number(suggestion["number"])[1] == letter
        ]
        candidates = exact or suggestions
        if not candidates:
            raise SourceArgumentNotFound(
                "address", self._address, "No collection schedule found"
            )
        response = self._session.get(
            f"{WEBSITE_URL}{candidates[0]['url']}&utskrift=1", timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response

    def _parse_website(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        entries = []
        seen = set()
        for pickup_list in soup.select("ul.navigationlist--pickup"):
            title = pickup_list.select_one("li.navigationlist__item--title")
            if title is None:
                continue
            name = title.get_text(strip=True)
            waste_type = WEBSITE_FRACTION_MAP.get(name, name)
            for item in pickup_list.select("li.navigationlist__item--pickup"):
                match = re.search(
                    "(\\d{1,2})\\.\\s*([a-zæøå]+)\\s+(\\d{4})",
                    item.get_text().casefold(),
                )
                if match is None or match.group(2) not in MONTHS:
                    continue
                date = datetime.date(
                    int(match.group(3)), MONTHS[match.group(2)], int(match.group(1))
                )
                if (date, waste_type) in seen:
                    continue
                seen.add((date, waste_type))
                entries.append({"date": date, "type": waste_type})
        if not entries:
            raise SourceArgumentNotFound(
                "address", self._address, "No collection schedule found"
            )
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
