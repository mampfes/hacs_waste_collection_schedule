from datetime import datetime
from typing import Any

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Gemeinde24"
DESCRIPTION = "Source for Gemeinde24 municipal app waste collection data"
COUNTRY = "at"
URL = "https://www.gemeinde24.at"
TEST_CASES = {
    "Gaal by IDs": {
        "gemeinde_id": "114",
        "street_id": "4321",
    },
    "Gaal by names": {
        "gemeinde": "Gaal",
        "strasse": "Gaal",
    },
}

API_BASE_URL = "https://www.gemeinde24.at/admin/API"
API_KEY = "justanapp"
APP_VERSION = "20251020"
REQUEST_TIMEOUT = 30
SEARCH_LATITUDE = "47.5000"
SEARCH_LONGITUDE = "14.5000"

ICON_MAP = {
    "rm": "mdi:trash-can",
    "bm": "mdi:leaf",
    "lf": "mdi:recycle",
    "ap": "mdi:package-variant",
    "ag": "mdi:glass-wine",
    "am": "mdi:iron-outline",
    "sp": "mdi:sofa",
    "gs": "mdi:tree",
    "ps": "mdi:chemical-weapon",
    "el": "mdi:flash",
    "frei1": "mdi:chemical-weapon",
    "frei2": "mdi:recycle-variant",
}

TITLE_ICON_MAP = {
    "restmuell": "mdi:trash-can",
    "biomuell": "mdi:leaf",
    "gelber sack": "mdi:recycle",
    "altpapier": "mdi:package-variant",
    "altglas": "mdi:glass-wine",
    "altmetall": "mdi:iron-outline",
    "sperrmuell": "mdi:sofa",
    "gruenschnitt": "mdi:tree",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the Gemeinde24 app flow: choose municipality, then choose street. "
        "You can configure either municipality/street names or the numeric IDs."
    ),
    "de": (
        "Nutzen Sie den Gemeinde24-Ablauf: zuerst Gemeinde wählen, dann Straße. "
        "Sie können entweder Namen oder die numerischen IDs eintragen."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "gemeinde": "Municipality name as shown in Gemeinde24.",
        "strasse": "Street/local area name as shown in Gemeinde24.",
        "gemeinde_id": (
            "Numeric GemeindeID from Gemeinde24 "
            "(optional alternative to the municipality field)."
        ),
        "street_id": (
            "Numeric streetID from Gemeinde24 "
            "(optional alternative to the street field)."
        ),
    },
    "de": {
        "gemeinde": "Gemeindename wie in Gemeinde24 angezeigt.",
        "strasse": "Strassen-/Ortsteilname wie in Gemeinde24 angezeigt.",
        "gemeinde_id": (
            "Numerische GemeindeID aus Gemeinde24 "
            "(optional statt des Gemeinde-Feldes)."
        ),
        "street_id": (
            "Numerische streetID aus Gemeinde24 " "(optional statt des Straßen-Feldes)."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "gemeinde": "Municipality",
        "strasse": "Street",
        "gemeinde_id": "Municipality ID",
        "street_id": "Street ID",
    },
    "de": {
        "gemeinde": "Gemeinde",
        "strasse": "Strasse",
        "gemeinde_id": "Gemeinde ID",
        "street_id": "Strassen ID",
    },
}


class Source:
    def __init__(
        self,
        gemeinde: str | None = None,
        strasse: str | None = None,
        gemeinde_id: str | int | None = None,
        street_id: str | int | None = None,
    ):
        self._gemeinde = self._clean(gemeinde)
        self._strasse = self._clean(strasse)
        self._gemeinde_id = self._clean(gemeinde_id)
        self._street_id = self._clean(street_id)

        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "g24_230827/251029 CFNetwork/3860.500.112 Darwin/25.4.0",
                "Accept": "*/*",
            }
        )

    def fetch(self) -> list[Collection]:
        gemeinde_id = self._resolve_gemeinde_id()
        street_id = self._resolve_street_id(gemeinde_id)

        payload = self._request_json(
            method="GET",
            endpoint="content2.php",
            params={
                "GemeindeID": gemeinde_id,
                "apiKEY": API_KEY,
                "StreetID": street_id,
                "appversion": APP_VERSION,
            },
        )

        waste_list = payload.get("waste_list.php")
        if not isinstance(waste_list, list):
            raise Exception(
                "Unexpected response from content2.php: missing or invalid 'waste_list.php'."
            )

        entries = []
        for item in waste_list:
            if not isinstance(item, dict):
                continue

            date_obj = self._parse_date(item.get("datum"))
            if date_obj is None:
                continue

            title = self._clean(item.get("title"))
            if not title:
                continue

            waste_id = self._clean(item.get("wasteID")).lower()
            icon = ICON_MAP.get(waste_id)
            if icon is None:
                icon = TITLE_ICON_MAP.get(self._normalize(title))

            entries.append(Collection(date=date_obj, t=title, icon=icon))

        return entries

    def _resolve_gemeinde_id(self) -> str:
        if self._gemeinde_id:
            return self._gemeinde_id

        if not self._gemeinde:
            raise SourceArgumentRequired(
                "gemeinde", "or provide 'gemeinde_id' as an alternative."
            )

        payload = self._request_json(
            method="POST",
            endpoint="gemeinden.php",
            params={"apiKEY": API_KEY},
            data={
                "lat": SEARCH_LATITUDE,
                "long": SEARCH_LONGITUDE,
                "apiKEY": API_KEY,
            },
        )

        if str(payload.get("code", "")).upper() != "OK":
            raise Exception("gemeinden.php did not return code 'OK'.")

        reports = payload.get("reports")
        if not isinstance(reports, list):
            raise Exception(
                "Unexpected response from gemeinden.php: missing 'reports'."
            )

        exact_matches_with_id: list[tuple[str, str, str]] = []
        all_names_with_id = []

        for report in reports:
            if not isinstance(report, dict):
                continue

            name = self._clean(report.get("Gemeindename"))
            this_gemeinde_id = self._clean(report.get("GemeindeID"))
            zip_code = self._clean(report.get("zip"))

            if not name:
                continue

            if this_gemeinde_id:
                all_names_with_id.append(name)

            if (
                self._normalize(name) == self._normalize(self._gemeinde)
                and this_gemeinde_id
            ):
                exact_matches_with_id.append((this_gemeinde_id, name, zip_code))

        if len(exact_matches_with_id) == 1:
            return exact_matches_with_id[0][0]

        if len(exact_matches_with_id) > 1:
            suggestions = [
                self._format_gemeinde_suggestion(match[0], match[1], match[2])
                for match in exact_matches_with_id
            ]
            raise SourceArgAmbiguousWithSuggestions(
                "gemeinde", self._gemeinde, self._deduplicate(suggestions)
            )

        raise SourceArgumentNotFoundWithSuggestions(
            "gemeinde",
            self._gemeinde,
            self._build_suggestions(self._gemeinde, all_names_with_id),
        )

    def _resolve_street_id(self, gemeinde_id: str) -> str:
        payload = self._request_json(
            method="GET",
            endpoint="wastesetup_v2.php",
            params={"GemeindeID": gemeinde_id, "apiKEY": API_KEY},
        )

        if str(payload.get("code", "")).upper() != "OK":
            raise Exception("wastesetup_v2.php did not return code 'OK'.")

        streets = payload.get("strassen")
        if not isinstance(streets, list):
            raise Exception(
                "Unexpected response from wastesetup_v2.php: missing 'strassen'."
            )

        street_pairs = []
        for street in streets:
            if not isinstance(street, dict):
                continue
            street_name = self._clean(street.get("street"))
            street_id = self._clean(street.get("streetID"))
            if street_name and street_id:
                street_pairs.append((street_name, street_id))

        if self._street_id:
            if any(street_id == self._street_id for _, street_id in street_pairs):
                return self._street_id

            raise SourceArgumentNotFoundWithSuggestions(
                "street_id",
                self._street_id,
                [
                    self._format_street_suggestion(name, sid)
                    for name, sid in street_pairs
                ],
            )

        if not self._strasse:
            raise SourceArgumentRequired(
                "strasse", "or provide 'street_id' as an alternative."
            )

        exact_matches = [
            (name, sid)
            for name, sid in street_pairs
            if self._normalize(name) == self._normalize(self._strasse)
        ]

        if len(exact_matches) == 1:
            return exact_matches[0][1]

        if len(exact_matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "strasse",
                self._strasse,
                [
                    self._format_street_suggestion(name, sid)
                    for name, sid in exact_matches
                ],
            )

        raise SourceArgumentNotFoundWithSuggestions(
            "strasse",
            self._strasse,
            self._build_suggestions(self._strasse, [name for name, _ in street_pairs]),
        )

    def _request_json(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{API_BASE_URL}/{endpoint}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise Exception(f"Failed request to '{endpoint}': {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise Exception(f"Invalid JSON response from '{endpoint}'.") from exc

        if not isinstance(payload, dict):
            raise Exception(f"Unexpected JSON payload type from '{endpoint}'.")

        return payload

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = value.casefold().strip()
        normalized = (
            normalized.replace("ß", "ss")
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
        )
        normalized = normalized.replace("-", " ")
        normalized = " ".join(normalized.split())
        return normalized

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    def _build_suggestions(self, value: str, candidates: list[str]) -> list[str]:
        unique_candidates = self._deduplicate(
            [candidate for candidate in candidates if candidate]
        )
        query = self._normalize(value)

        if not unique_candidates:
            return []

        starts_with = [
            candidate
            for candidate in unique_candidates
            if self._normalize(candidate).startswith(query)
        ]
        contains = [
            candidate
            for candidate in unique_candidates
            if query and query in self._normalize(candidate)
        ]

        ordered = self._deduplicate(starts_with + contains + unique_candidates)
        return ordered[:20]

    @staticmethod
    def _format_gemeinde_suggestion(gemeinde_id: str, name: str, zip_code: str) -> str:
        if zip_code:
            return f"{name} ({zip_code}, GemeindeID={gemeinde_id})"
        return f"{name} (GemeindeID={gemeinde_id})"

    @staticmethod
    def _format_street_suggestion(name: str, street_id: str) -> str:
        return f"{name} (streetID={street_id})"

    @staticmethod
    def _parse_date(raw_date: Any):
        if not isinstance(raw_date, str):
            return None

        # Expected format from API: 'Fr-2026-04-24'
        _, separator, date_value = raw_date.partition("-")
        if not separator or not date_value:
            return None

        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            return None
