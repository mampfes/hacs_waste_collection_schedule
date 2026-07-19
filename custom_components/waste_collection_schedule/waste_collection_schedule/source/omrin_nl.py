"""Waste collection schedule source for Omrin."""

import uuid
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Omrin"
DESCRIPTION = "Source for Omrin waste collection schedules."
URL = "https://www.omrin.nl"
COUNTRY = "nl"
MUNICIPALITIES = (
    "Achtkarspelen",
    "Ameland",
    "Eemsdelta",
    "Elburg",
    "Ermelo",
    "Harderwijk",
    "Harlingen",
    "Heerenveen",
    "Het Hogeland",
    "Leeuwarden",
    "Nunspeet",
    "Oldebroek",
    "Ooststellingwerf",
    "Opsterland",
    "Pekela",
    "Schiermonnikoog",
    "Terschelling",
    "Tytsjerksteradiel",
    "Waadhoeke",
    "Westerwolde",
    "Weststellingwerf",
)

EXTRA_INFO = [
    {"title": municipality, "url": URL, "country": COUNTRY}
    for municipality in MUNICIPALITIES
]
TEST_CASES = {
    "Weme 3, Ermelo": {
        "postal_code": "3851MA",
        "house_number": "3",
        "suffix": "",
    },
}

BASE_URL = "https://api.omrinafvalapp.nl"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
GRAPHQL_URL = f"{BASE_URL}/graphql"

LOGIN_USER_AGENT = "Omrin.Afvalapp.Client/1.0"
GRAPHQL_USER_AGENT = "GraphQL.Client/6.1.0.0"

FETCH_CALENDAR_QUERY = """
query FetchCalendar {
  fetchCalendar {
    id
    date
    description
    type
    containerType
    placingTime
    state
  }
}
"""

ICON_MAP = {
    "GFT": Icons.ORGANIC,
    "PAPIER": Icons.PAPER,
    "PMD": Icons.RECYCLING,
    "RESTAFVAL": Icons.GENERAL_WASTE,
    "Sortibak": Icons.GENERAL_WASTE,
}
DEFAULT_ICON = Icons.GENERAL_WASTE
SENTINEL_DATE = "0001-01-01T00:00:00"
REQUEST_TIMEOUT = 30

PARAM_TRANSLATIONS = {
    "en": {
        "postal_code": "Postcode",
        "house_number": "House number",
        "suffix": "House number suffix",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "postal_code": "Dutch postcode, for example 3851MA.",
        "house_number": "Numeric house number.",
        "suffix": "House number suffix, if applicable.",
    }
}


class Source:
    """Fetch Omrin collections using a fresh anonymous app session."""

    def __init__(
        self, postal_code: str, house_number: str | int, suffix: str = ""
    ) -> None:
        self._postal_code = postal_code
        try:
            self._house_number = int(house_number)
        except (TypeError, ValueError) as exc:
            raise SourceArgumentException(
                "house_number", "House number must be numeric."
            ) from exc
        self._suffix = suffix

    def fetch(self) -> list[Collection]:
        """Log in anonymously and fetch the collection calendar."""
        device_id = str(uuid.uuid4())
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": LOGIN_USER_AGENT,
                "Accept": "application/json",
            }
        )

        login_response = session.post(
            LOGIN_URL,
            json={
                "Email": None,
                "Password": None,
                "PostalCode": self._postal_code,
                "HouseNumber": self._house_number,
                "HouseNumberExtension": self._suffix,
                "DeviceId": device_id,
                "Platform": "iOS",
                "AppVersion": "4.0.3.273",
                "OsVersion": "iPhone15,3 26.2.1",
            },
            timeout=REQUEST_TIMEOUT,
        )
        login_response.raise_for_status()

        try:
            login_payload = login_response.json()
        except ValueError as exc:
            raise RuntimeError("Omrin login returned malformed JSON") from exc

        if not isinstance(login_payload, dict) or not login_payload.get("success"):
            errors = (
                login_payload.get("errors", "unknown error")
                if isinstance(login_payload, dict)
                else "malformed response"
            )
            raise RuntimeError(f"Omrin login failed: {errors}")

        login_data = login_payload.get("data")
        access_token = (
            login_data.get("accessToken") if isinstance(login_data, dict) else None
        )
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeError("Omrin login response did not contain an access token")

        calendar_response = session.post(
            GRAPHQL_URL,
            headers={
                "Content-Type": "application/json",
                "User-Agent": GRAPHQL_USER_AGENT,
                "Authorization": f"Bearer {access_token}",
            },
            json={"query": FETCH_CALENDAR_QUERY},
            timeout=REQUEST_TIMEOUT,
        )
        calendar_response.raise_for_status()

        try:
            calendar_payload = calendar_response.json()
        except ValueError as exc:
            raise RuntimeError("Omrin calendar returned malformed JSON") from exc

        if not isinstance(calendar_payload, dict):
            raise RuntimeError("Omrin calendar response was malformed")

        graphql_errors = calendar_payload.get("errors")
        if graphql_errors:
            if isinstance(graphql_errors, list):
                messages = [
                    error.get("message", str(error))
                    if isinstance(error, dict)
                    else str(error)
                    for error in graphql_errors
                ]
                error_detail = ", ".join(messages)
            else:
                error_detail = str(graphql_errors)
            raise RuntimeError(f"Omrin GraphQL error: {error_detail}")

        data = calendar_payload.get("data")
        calendar = data.get("fetchCalendar") if isinstance(data, dict) else None
        if not isinstance(calendar, list):
            raise RuntimeError("Omrin calendar response was malformed")

        entries: list[Collection] = []
        for item in calendar:
            if not isinstance(item, dict):
                raise RuntimeError(
                    "Omrin calendar response contained a malformed entry"
                )

            raw_date = item.get("date")
            if not raw_date or raw_date == SENTINEL_DATE:
                continue

            waste_type = item.get("type")
            if not isinstance(waste_type, str) or not waste_type:
                continue

            try:
                collection_date = datetime.fromisoformat(
                    str(raw_date).replace("Z", "+00:00")
                ).date()
            except (TypeError, ValueError):
                continue

            collection = Collection(
                date=collection_date,
                t=waste_type,
                icon=ICON_MAP.get(waste_type, DEFAULT_ICON),
            )
            if collection not in entries:
                entries.append(collection)

        return entries
