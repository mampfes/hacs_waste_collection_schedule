import re
from collections.abc import Sequence
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, cast

from curl_cffi.const import CurlHttpVersion

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_DOMAINS = (
    "https://apps.cloud9apps.com",
    "https://apps.cloud9technologies.com",
)
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

Address = dict[str, Any]
JSONDict = dict[str, Any]


def normalise_postcode(text: str | None) -> str | None:
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


def _parse_date_string(value: Any) -> date | None:
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


def _extract_dates(details: dict[str, Any]) -> list[date]:
    values: list[Any] = [
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
    next_collection = cast(dict[str, Any], details.get("nextCollection") or {})
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
) -> list[tuple[str, dict[str, Any]]]:
    collections_section = cast(
        dict[str, dict[str, Any]] | None, collection_data.get("collections")
    )
    if collections_section:
        return list(collections_section.items())
    items: list[tuple[str, dict[str, Any]]] = []
    for key, value in collection_data.items():
        if not key.lower().endswith("collectiondetails"):
            continue
        if isinstance(value, list):
            for idx, entry in enumerate(value, start=1):
                if entry:
                    items.append((f"{key}_{idx}", cast(dict[str, Any], entry)))
        elif value:
            items.append((key, cast(dict[str, Any], value)))
    return items


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# The Cloud9 citizen-mobile API (apps.cloud9apps.com / apps.cloud9technologies.com)
# returns one property's collection schedule keyed by UPRN. A council source
# either supplies a UPRN directly or a postcode (plus optional address parts) that
# is resolved to a UPRN via the ``/addresses`` lookup. All of that is acquisition
# (HTTP across two mirror domains, plus the address match) and lives in
# Cloud9Retriever; Cloud9Parser does no I/O, turning the raw
# ``wasteCollectionDates`` payload into ``(date, label)`` rows. Each source then
# maps its own container labels onto canonical waste types with a RowTransformer.
# --------------------------------------------------------------------------- #


class Cloud9Retriever(RetrieverFunc):
    """Resolve a property and return its raw Cloud9 waste payload.

    Args are the ``source.params`` field names holding the property identifiers
    for this council (the wire names differ per source):

    * ``uprn_field``: when set and populated, the UPRN is used directly and no
      address lookup happens.
    * ``postcode_field`` / ``name_number_field`` / ``street_field`` /
      ``town_field``: the address-lookup inputs; the postcode drives the
      ``/addresses`` query and the rest refine the best-match scoring.
    * ``address_field``: a single free-text address string (used verbatim as the
      match query) instead of the separate name/street/town parts.
    * ``argument_name``: the config argument a lookup failure is reported against.

    The Cloud9 API is fronted by an AWS ELB that sometimes echoes HTTP/1.1-only
    response headers (e.g. ``keep-alive: timeout=5``) on an HTTP/2 connection.
    That violates RFC 7540 8.1.2.2 and makes curl_cffi/nghttp2 abort with
    CurlError 92. Every request is therefore forced to HTTP/1.1 on the shared
    ``source.session``.
    """

    def __init__(
        self,
        authority: str,
        *,
        uprn_field: str | None = None,
        postcode_field: str | None = None,
        name_number_field: str | None = None,
        street_field: str | None = None,
        town_field: str | None = None,
        address_field: str | None = None,
        argument_name: str = "postcode",
        api_domains: Sequence[str] | None = None,
    ):
        self.authority = authority
        self.uprn_field = uprn_field
        self.postcode_field = postcode_field
        self.name_number_field = name_number_field
        self.street_field = street_field
        self.town_field = town_field
        self.address_field = address_field
        self.argument_name = argument_name
        configured_domains = API_DOMAINS if api_domains is None else api_domains
        self._base_urls = [
            f"{domain.rstrip('/')}/{authority}{API_BASE}"
            for domain in configured_domains
            if domain and domain.strip()
        ]
        if not self._base_urls:
            raise ValueError("At least one API domain must be configured.")

    def __call__(self, source: "BaseSource") -> JSONDict:
        params = source.params

        uprn = params.get(self.uprn_field) if self.uprn_field else None
        if uprn:
            return self._fetch_waste(source, str(uprn))

        postcode = params.get(self.postcode_field) if self.postcode_field else None
        name_number = (
            params.get(self.name_number_field) if self.name_number_field else None
        )
        street = params.get(self.street_field) if self.street_field else None
        town = params.get(self.town_field) if self.town_field else None

        if self.address_field:
            address_string = str(params.get(self.address_field) or "")
        else:
            address_string = " ".join(
                part.strip()
                for part in (name_number, street, town, postcode)
                if isinstance(part, str) and part.strip()
            )

        normalised = normalise_postcode(postcode)
        addresses = self._lookup_addresses(
            source,
            postcode=postcode,
            normalised_postcode=normalised,
            address_name_number=name_number,
            address_street=street,
            address_string=address_string,
        )
        selected = self._select_address(
            addresses,
            address_string=address_string,
            normalised_postcode=normalised,
            address_name_number=name_number,
            address_street=street,
            street_town=town,
        )
        selected_uprn = selected.get("uprn")
        if not selected_uprn:
            raise SourceArgumentNotFound(
                self.argument_name,
                address_string,
                "the selected address does not expose a UPRN.",
            )
        return self._fetch_waste(source, str(selected_uprn))

    def _fetch_waste(self, source: "BaseSource", uprn: str) -> JSONDict:
        return self._request_json(source, f"{WASTE_PATH}/{uprn}")

    def _request_json(
        self,
        source: "BaseSource",
        path: str,
        params: dict[str, str] | None = None,
    ) -> JSONDict:
        # The two API domains mirror each other; try each in turn and fall
        # through to the next on ANY failure (DNS, TLS, connection, a bad HTTP
        # status, or an offline-fixture replay miss for a domain that was
        # unreachable at recording time), raising only if every domain fails.
        last_error: Exception | None = None
        for base_url in self._base_urls:
            try:
                response = source.session.get(
                    f"{base_url}{path}",
                    params=params,
                    headers=BASE_HEADERS,
                    http_version=CurlHttpVersion.V1_1,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                return cast(JSONDict, response.json())
            except Exception as err:
                last_error = err
        assert last_error is not None
        raise last_error

    def _lookup_addresses(
        self,
        source: "BaseSource",
        postcode: str | None,
        normalised_postcode: str | None,
        address_name_number: str | None,
        address_street: str | None,
        address_string: str,
    ) -> list[Address]:
        address_line = " ".join(
            part.strip()
            for part in (address_name_number, address_street)
            if isinstance(part, str) and part.strip()
        )

        seen: set[tuple[str, str]] = set()
        attempts: list[tuple[str, str | None]] = [
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
            payload_json = self._request_json(
                source,
                ADDRESSES_PATH,
                params={param: cleaned},
            )
            addresses_data = cast(list[Address] | None, payload_json.get("addresses"))
            if addresses_data:
                return [cast(Address, a) for a in addresses_data]

        raise SourceArgumentNotFound(
            self.argument_name,
            postcode or address_string,
            "no matching addresses were returned by the API.",
        )

    def _select_address(
        self,
        addresses: Sequence[Address],
        address_string: str,
        normalised_postcode: str | None,
        address_name_number: str | None,
        address_street: str | None,
        street_town: str | None,
    ) -> Address:
        query_lower = address_string.lower() if address_string else ""
        postcode_lower = normalised_postcode.lower() if normalised_postcode else None

        scored: list[tuple[int, Address]] = []
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
                argument=self.argument_name,
                value=address_string,
                suggestions=suggestions,
            )

        top = [addr for s, addr in scored if s == best_score]
        if len(top) > 1:
            suggestions = [_address_to_string(a) for a in top]
            raise SourceArgAmbiguousWithSuggestions(
                argument=self.argument_name,
                value=address_string,
                suggestions=suggestions,
            )

        return top[0]


class Cloud9Parser(Parser["list[tuple[date, str]]"]):
    """Decode a raw ``wasteCollectionDates`` payload into ``(date, label)`` rows.

    Does no I/O, so it runs standalone against a cached payload fixture. Each
    distinct ``(date, container-label)`` pair becomes one row; the source's
    RowTransformer then maps the label onto a canonical waste type.
    """

    def __call__(
        self,
        raw: JSONDict,
        source: "BaseSource | None" = None,
    ) -> "list[tuple[date, str]]":
        response_shape.expect(
            isinstance(raw, dict),
            source_name=response_shape.source_name(source),
            detail="Cloud9 response is not a JSON object",
            raw=raw,
        )

        collection_data = cast(
            JSONDict,
            raw.get("wasteCollectionDates") or raw.get("WasteCollectionDates") or raw,
        )

        rows: list[tuple[date, str]] = []
        seen: set[tuple[date, str]] = set()
        for key, details in _collection_items(collection_data):
            if not details:
                continue
            raw_label = (
                details.get("containerDescription")
                or details.get("containerName")
                or details.get("collectionType")
                or key
            )
            label = raw_label if isinstance(raw_label, str) else str(raw_label)
            for collection_date in _extract_dates(details):
                identifier = (collection_date, label)
                if identifier in seen:
                    continue
                seen.add(identifier)
                rows.append(identifier)

        rows.sort(key=lambda row: row[0])
        return rows
