import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, cast

import requests

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

API_DOMAIN = "https://apps.cloud9technologies.com"
API_BASE = "/citizenmobile/mobileapi"
ADDRESSES_PATH = "/addresses"
WASTE_PATH = "/wastecollections"
REQUEST_TIMEOUT = 30

BASIC_TOKEN = "Y2xvdWQ5OmlkQmNWNGJvcjU="
BASE_HEADERS = {
    "Authorization": f"Basic {BASIC_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-api-version": "2",
}

POSTCODE_PATTERN = re.compile(r"([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})", re.IGNORECASE)
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

ADDRESS_FIELDS = (
    "fullAddress",
    "singleLineAddress",
    "address",
    "addressLine1",
    "addressLine2",
    "addressLine3",
    "town",
    "buildingName",
    "buildingNumber",
    "propertyNumber",
    "street",
    "postcode",
)

Address = Dict[str, Any]
JSONDict = Dict[str, Any]


def normalise_postcode(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = POSTCODE_PATTERN.search(text)
    if not match:
        return None
    return f"{match.group(1).upper()} {match.group(2).upper()}"


def _address_to_string(address: Address) -> str:
    return " ".join(
        str(value)
        for key in ADDRESS_FIELDS
        for value in [address.get(key)]
        if value not in (None, "")
    ).strip()


def _clean_type_name(name: str) -> str:
    cleaned = name.strip()
    if cleaned.lower().endswith("collection"):
        cleaned = cleaned[: -len("collection")].strip()
    if cleaned.lower().endswith("bins"):
        cleaned = cleaned[: -len("bins")].strip()
    elif cleaned.lower().endswith("bin"):
        cleaned = cleaned[: -len("bin")].strip()
    return cleaned or name


def _parse_date_string(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    iso_candidate = candidate
    if iso_candidate.endswith("Z"):
        iso_candidate = iso_candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(iso_candidate).date()
    except ValueError:
        pass
    iso_match = ISO_DATE_PATTERN.search(candidate)
    if iso_match:
        try:
            return datetime.strptime(iso_match.group(), "%Y-%m-%d").date()
        except ValueError:
            pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


def _extract_dates(details: Dict[str, Any]) -> List[date]:
    values: List[Any] = [
        details.get(key)
        for key in ("collectionDate", "nextCollectionDate", "nextCollection")
    ]
    values.extend(details.get("collectionDates") or [])
    values.extend(
        (
            (
                entry.get("collectionDate")
                or entry.get("nextCollectionDate")
                or entry.get("date")
            )
            if isinstance(entry, dict)
            else entry
        )
        for entry in details.get("futureCollections") or []
    )
    next_collection = cast(Dict[str, Any], details.get("nextCollection") or {})
    values.append(
        next_collection.get("collectionDate")
        or next_collection.get("nextCollectionDate")
        or next_collection.get("date")
    )

    return sorted(
        {parsed for parsed in map(_parse_date_string, values) if parsed is not None}
    )


def _collection_items(
    collection_data: JSONDict,
) -> List[Tuple[str, Dict[str, Any]]]:
    collections_section = cast(
        Optional[Dict[str, Dict[str, Any]]], collection_data.get("collections")
    )
    if collections_section:
        return list(collections_section.items())
    items: List[Tuple[str, Dict[str, Any]]] = []
    for key, value in collection_data.items():
        if not key.lower().endswith("collectiondetails"):
            continue
        if isinstance(value, list):
            for idx, entry in enumerate(value, start=1):
                if entry:
                    items.append((f"{key}_{idx}", cast(Dict[str, Any], entry)))
        elif value:
            items.append((key, cast(Dict[str, Any], value)))
    return items


class Cloud9Client:
    def __init__(
        self,
        authority: str,
        icon_keywords: Optional[Dict[str, str]] = None,
    ):
        self._authority = authority
        self._icon_keywords: Dict[str, str] = icon_keywords or {}
        self._base_url = f"{API_DOMAIN}/{authority}{API_BASE}"

    def _resolve_icon(self, label: str) -> Optional[str]:
        lowered = label.lower()
        for keyword, icon in self._icon_keywords.items():
            if keyword in lowered:
                return icon
        return None

    def _build_collections(self, payload: JSONDict) -> List[Collection]:
        collection_data = cast(
            JSONDict,
            payload.get("wasteCollectionDates")
            or payload.get("WasteCollectionDates")
            or payload,
        )

        entries: List[Collection] = []
        seen: Set[Tuple[date, str]] = set()

        for key, details in _collection_items(collection_data):
            if not details:
                continue
            raw_label = (
                details.get("containerDescription")
                or details.get("containerName")
                or details.get("collectionType")
                or key
            )
            if not isinstance(raw_label, str):
                raw_label = str(raw_label)
            label = _clean_type_name(raw_label)
            icon = self._resolve_icon(label)
            for collection_date in _extract_dates(details):
                identifier = (collection_date, label)
                if identifier in seen:
                    continue
                seen.add(identifier)
                entries.append(Collection(date=collection_date, t=label, icon=icon))

        return entries

    def _fetch_waste_json(self, session: requests.Session, uprn: str) -> JSONDict:
        url = f"{self._base_url}{WASTE_PATH}/{uprn}"
        response = session.get(url, headers=dict(BASE_HEADERS), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return cast(JSONDict, response.json())

    def fetch_by_uprn(self, uprn: str) -> List[Collection]:
        session = requests.Session()
        payload = self._fetch_waste_json(session, uprn)
        entries = self._build_collections(payload)
        entries.sort(key=lambda item: item.date)
        return entries

    def fetch_by_address(
        self,
        postcode: Optional[str],
        address_string: str,
        address_name_number: Optional[str] = None,
        address_street: Optional[str] = None,
        street_town: Optional[str] = None,
        argument_name: str = "address_postcode",
    ) -> List[Collection]:
        session = requests.Session()
        headers = dict(BASE_HEADERS)
        normalised = normalise_postcode(postcode)

        addresses = self._lookup_addresses(
            session,
            headers,
            postcode=postcode,
            normalised_postcode=normalised,
            address_name_number=address_name_number,
            address_street=address_street,
            address_string=address_string,
        )
        selected = self._select_address(
            addresses,
            address_string=address_string,
            normalised_postcode=normalised,
            address_name_number=address_name_number,
            address_street=address_street,
            street_town=street_town,
            argument_name=argument_name,
        )
        uprn = selected.get("uprn")
        if not uprn:
            raise ValueError("Selected address does not expose a UPRN.")

        entries = self.fetch_by_uprn(uprn)
        if not entries:
            raise ValueError("No collection data returned for the selected address.")
        return entries

    def _lookup_addresses(
        self,
        session: requests.Session,
        headers: Dict[str, str],
        postcode: Optional[str],
        normalised_postcode: Optional[str],
        address_name_number: Optional[str],
        address_street: Optional[str],
        address_string: str,
    ) -> List[Address]:
        url = f"{self._base_url}{ADDRESSES_PATH}"

        address_line = " ".join(
            part.strip()
            for part in (address_name_number, address_street)
            if isinstance(part, str) and part.strip()
        )

        seen: Set[Tuple[str, str]] = set()
        attempts: List[Tuple[str, Optional[str]]] = [
            ("postcode", normalised_postcode),
            ("postcode", postcode),
            ("address", address_string),
            ("query", address_string),
            ("address", address_line),
            ("query", address_line),
            ("query", address_street),
        ]
        for param, value in attempts:
            cleaned = (value or "").strip()
            if not cleaned:
                continue
            key = (param, cleaned.lower())
            if key in seen:
                continue
            seen.add(key)
            response = session.get(
                url,
                headers=headers,
                params={param: cleaned},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload_json = cast(JSONDict, response.json())
            addresses_data = cast(
                Optional[List[Address]], payload_json.get("addresses")
            )
            if addresses_data:
                return [cast(Address, a) for a in addresses_data]

        raise ValueError("No matching addresses were returned by the API.")

    def _select_address(
        self,
        addresses: Sequence[Address],
        address_string: str,
        normalised_postcode: Optional[str],
        address_name_number: Optional[str],
        address_street: Optional[str],
        street_town: Optional[str],
        argument_name: str,
    ) -> Address:
        if not addresses:
            raise ValueError("Address lookup returned no results.")

        query_lower = address_string.lower() if address_string else ""
        postcode_lower = normalised_postcode.lower() if normalised_postcode else None

        scored: List[Tuple[int, Address]] = []
        for address in addresses:
            full = _address_to_string(address)
            lowered = full.lower()
            score = 0

            candidate_postcode = normalise_postcode(address.get("postcode"))
            if (
                postcode_lower
                and candidate_postcode
                and candidate_postcode.lower() == postcode_lower
            ):
                score += 100
            elif postcode_lower and postcode_lower in lowered:
                score += 60

            if address_street and address_street.lower() in lowered:
                score += 30

            if address_name_number:
                number = str(address_name_number).strip().lower()
                if re.search(rf"\b{re.escape(number)}\b", lowered):
                    score += 25

            if street_town and street_town.lower() in lowered:
                score += 15

            if query_lower and re.search(
                rf"(?:^|\b){re.escape(query_lower)}(?:\b|$)", lowered
            ):
                score += 10

            scored.append((score, address))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score = scored[0][0]

        if best_score <= 0:
            suggestions = [_address_to_string(a) for a in addresses]
            raise SourceArgumentNotFoundWithSuggestions(
                argument=argument_name,
                value=address_string,
                suggestions=suggestions,
            )

        top = [addr for s, addr in scored if s == best_score]
        if len(top) > 1:
            suggestions = [_address_to_string(a) for a in top]
            raise SourceArgAmbiguousWithSuggestions(
                argument=argument_name,
                value=address_string,
                suggestions=suggestions,
            )

        return top[0]
