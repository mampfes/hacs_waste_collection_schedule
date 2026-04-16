import datetime
import re
from typing import Any

from curl_cffi import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Enfield Council"
DESCRIPTION = "Source for Enfield Council, London, UK."
URL = "https://www.enfield.gov.uk/services/rubbish-and-recycling/find-my-collection-day"
COUNTRY = "uk"
TEST_CASES = {
    "uprn": {"uprn": "207102166"},
    "address": {"address": "127 Palmerston Rd, London N22 8QX"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your address on the Enfield Council collection-day page. "
        "If address lookup is ambiguous, use your UPRN from "
        "[Find My Address](https://www.findmyaddress.co.uk/)."
    )
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "address": "Full address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Use your UPRN if you know it.",
        "address": (
            "Full Enfield address, for example " "'127 Palmerston Rd, London N22 8QX'."
        ),
    }
}

LOOKUP_URL = "https://www.enfield.gov.uk/_design/integrations/ordnance-survey/places-v2"
SCHEDULE_URL = "https://www.enfield.gov.uk/_design/integrations/bartec/find-my-collection/rest/schedule"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": URL,
}

ABBREVIATIONS = {
    " RD ": " ROAD ",
    " ST ": " STREET ",
    " AVE ": " AVENUE ",
    " AV ": " AVENUE ",
    " LN ": " LANE ",
    " DR ": " DRIVE ",
    " CL ": " CLOSE ",
    " CT ": " COURT ",
    " PL ": " PLACE ",
}

POSTCODE_PATTERN = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.IGNORECASE)
HOUSE_NUMBER_PATTERN = re.compile(r"^\s*([0-9]+[A-Z]?(?:-[0-9A-Z]+)?)\b", re.IGNORECASE)

TYPE_KEYWORDS = {
    "FOOD": ("Food Waste", "mdi:food-apple"),
    "RECYCL": ("Recycling", "mdi:recycle"),
    "RESIDUAL": ("General Waste", "mdi:trash-can"),
    "REFUSE": ("General Waste", "mdi:trash-can"),
    "GARDEN": ("Garden Waste", "mdi:leaf"),
}


class Source:
    def __init__(self, uprn: str | int | None = None, address: str | None = None):
        self._uprn = str(uprn).strip() if uprn is not None else None
        self._address = address.strip() if address else None
        if not self._uprn and not self._address:
            raise SourceArgumentExceptionMultiple(
                ["uprn", "address"],
                "Provide either a UPRN or a full Enfield address.",
            )
        if self._uprn and not self._uprn.isdigit():
            raise SourceArgumentException("uprn", "UPRN must be numeric.")

        self._session = requests.Session(impersonate="chrome124")
        self._session.headers.update(HEADERS)

    def fetch(self) -> list[Collection]:
        self._bootstrap_session()
        uprn = self._uprn or self._resolve_uprn(self._address or "")
        response = self._session.get(
            SCHEDULE_URL, params={"uprn": uprn}, timeout=30, headers=HEADERS
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            raise SourceArgumentNotFound(
                "uprn", uprn, "no collection data was returned for this property."
            )

        entries: list[Collection] = []
        for item in data:
            scheduled_start = self._get_nested_text(item, "ScheduledStart")
            job_name = self._get_nested_text(item, "JobName") or self._get_nested_text(
                item, "Description"
            )
            if not scheduled_start or not job_name:
                continue

            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        scheduled_start, "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    t=self._normalize_waste_type(job_name),
                    icon=self._icon_for_type(job_name),
                )
            )

        if not entries:
            raise SourceArgumentNotFound("uprn", uprn)

        return entries

    def _bootstrap_session(self) -> None:
        response = self._session.get(URL, timeout=30)
        response.raise_for_status()

    def _resolve_uprn(self, address: str) -> str:
        response = self._session.get(
            LOOKUP_URL, params={"query": address}, timeout=30, headers=HEADERS
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            raise SourceArgumentNotFound(
                "address", address, "no Enfield addresses matched this search."
            )

        exact_matches: list[dict[str, Any]] = []
        suggestions: list[str] = []
        normalized_address = self._normalize_address(address)

        for result in results:
            lpi = result.get("LPI", {})
            display_address = lpi.get("ADDRESS")
            if display_address:
                suggestions.append(display_address.title())
            if self._matches_address(normalized_address, lpi):
                exact_matches.append(lpi)

        if len(exact_matches) == 1:
            return exact_matches[0]["UPRN"]
        if len(exact_matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                address,
                [self._format_suggestion(item) for item in exact_matches[:5]],
            )

        unique_suggestions = list(dict.fromkeys(suggestions))
        if unique_suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", address, unique_suggestions[:5]
            )
        raise SourceArgumentNotFound("address", address)

    @staticmethod
    def _get_nested_text(item: dict[str, Any], key: str) -> str | None:
        value = item.get(key)
        if isinstance(value, dict):
            return value.get("_text")
        if isinstance(value, str):
            return value
        return None

    @classmethod
    def _normalize_address(cls, value: str) -> str:
        normalized = f" {value.upper()} "
        normalized = normalized.replace(",", " ")
        normalized = re.sub(r"\s+", " ", normalized)
        for source, target in ABBREVIATIONS.items():
            normalized = normalized.replace(source, target)
        return normalized.strip()

    @classmethod
    def _matches_address(cls, normalized_input: str, lpi: dict[str, Any]) -> bool:
        candidate_full = cls._normalize_address(lpi.get("ADDRESS", ""))
        candidate_key = cls._normalize_address(
            " ".join(
                part
                for part in [
                    lpi.get("PAO_START_NUMBER", ""),
                    lpi.get("PAO_START_SUFFIX", ""),
                    lpi.get("STREET_DESCRIPTION", ""),
                    lpi.get("POSTCODE_LOCATOR", ""),
                ]
                if part
            )
        )
        postcode = cls._extract_postcode(normalized_input)
        house_number = cls._extract_house_number(normalized_input)
        candidate_postcode = cls._normalize_address(lpi.get("POSTCODE_LOCATOR", ""))
        candidate_house_number = cls._normalize_address(
            str(lpi.get("PAO_START_NUMBER", ""))
        )
        candidate_street = cls._normalize_address(lpi.get("STREET_DESCRIPTION", ""))
        return (
            candidate_full == normalized_input
            or candidate_key == normalized_input
            or candidate_key in normalized_input
            or normalized_input in candidate_full
            or (
                bool(postcode)
                and bool(house_number)
                and postcode == candidate_postcode
                and house_number == candidate_house_number
                and bool(candidate_street)
                and candidate_street in normalized_input
            )
        )

    @staticmethod
    def _format_suggestion(lpi: dict[str, Any]) -> str:
        return lpi.get("ADDRESS", "").title()

    @staticmethod
    def _extract_postcode(value: str) -> str:
        match = POSTCODE_PATTERN.search(value)
        if not match:
            return ""
        return Source._normalize_address(match.group(1))

    @staticmethod
    def _extract_house_number(value: str) -> str:
        match = HOUSE_NUMBER_PATTERN.match(value)
        if not match:
            return ""
        return Source._normalize_address(match.group(1))

    @staticmethod
    def _normalize_waste_type(job_name: str) -> str:
        upper_name = job_name.upper()
        for keyword, (label, _) in TYPE_KEYWORDS.items():
            if keyword in upper_name:
                return label
        cleaned = re.sub(r"^EMPTY BIN\s+", "", job_name, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def _icon_for_type(job_name: str) -> str | None:
        upper_name = job_name.upper()
        for keyword, (_, icon) in TYPE_KEYWORDS.items():
            if keyword in upper_name:
                return icon
        return None
