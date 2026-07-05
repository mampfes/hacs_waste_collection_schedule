import re
from datetime import date, datetime, timedelta, timezone

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Aneby Miljö & Vatten"
DESCRIPTION = "Source for Aneby Miljö & Vatten waste collection schedules."
URL = "https://aen.minasidor.info/"
COUNTRY = "se"
TEST_CASES = {
    "Nassjo": {
        "email": "!secret aen_minasidor_se_email",
        "password": "!secret aen_minasidor_se_password",
        "address": "!secret aen_minasidor_se_address",
    },
}

BASE_URL = "https://aen.minasidor.info"
CSRF_URL = f"{BASE_URL}/api/auth/csrf"
LOGIN_URL = f"{BASE_URL}/api/auth/callback/email"
SESSION_URL = f"{BASE_URL}/api/auth/session"
PICKUPS_URL = (
    "https://fpservice.bmsystem.se/1802Nassjo/"
    "CustomerDataProvider.svc/GetPickupAddresses"
)
API_URL = (
    "https://fpservice.bmsystem.se/1802Nassjo/"
    "CustomerDataProvider.svc/GetCalendarAndHistory"
)

PARAM_TRANSLATIONS = {
    "en": {
        "email": "Email address",
        "password": "Password",
        "address": "Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "email": "Email address used to log in to AEN Mina Sidor.",
        "password": "Password used to log in to AEN Mina Sidor.",
        "address": "Address to use when the account has more than one property.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Use the email address and password for AEN Mina Sidor. The source "
    "automatically finds the collection point. If your account has multiple "
    "properties, select the address shown in the configuration flow.",
}

ICON_MAP = {
    "Rest/Mat": Icons.GENERAL_WASTE,
    "Papper/Plast": Icons.RECYCLING,
}

_DATE_PATTERN = re.compile(r"^/Date\((-?\d+)([+-]\d{4})?\)/$")


class Source:
    def __init__(self, email: str, password: str, address: str | None = None):
        self._email = (email or "").strip()
        if not self._email:
            raise SourceArgumentRequired("email", "An email address is required.")
        if not password:
            raise SourceArgumentRequired("password", "A password is required.")
        self._password = password
        self._address = address.strip() if address else None

    def fetch(self) -> list[Collection]:
        today = date.today()
        access_token = self._get_access_token()
        pickup_ids = self._get_pickup_ids(access_token)

        entries = []
        for pickup_id in pickup_ids:
            response = requests.get(
                API_URL,
                params={
                    "dateStart": today.isoformat(),
                    "dateEnd": (today + timedelta(days=365)).isoformat(),
                    "pickupId": pickup_id,
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30,
            )
            response.raise_for_status()

            data = response.json().get("d") or {}
            for job in data.get("Jobs", []):
                calendar = job.get("Calendar") or {}
                execution_date = _parse_date(calendar.get("ExecutionDate", ""))
                if execution_date is None or execution_date < today:
                    continue

                waste_type = calendar.get("ContentType", "").strip()
                container_type = calendar.get("ContainerType", "").strip()
                if not waste_type:
                    continue

                entries.append(
                    Collection(
                        date=execution_date,
                        t=f"{container_type}: {waste_type}"
                        if container_type
                        else waste_type,
                        icon=ICON_MAP.get(waste_type, Icons.GENERAL_WASTE),
                    )
                )

        return entries

    def _get_pickup_ids(self, access_token: str) -> list[str]:
        response = requests.get(
            PICKUPS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json().get("d") or {}
        pickup_addresses = data.get("PickupAddresses", [])
        addresses: dict[str, list[str]] = {}
        for pickup in pickup_addresses:
            address = pickup.get("Address", "").strip()
            pickup_id = pickup.get("PickupId", "").strip()
            if address and pickup_id:
                addresses.setdefault(address, []).append(pickup_id)

        if not addresses:
            raise SourceArgumentNotFound(
                "address",
                self._address or "",
                "no collection points were returned",
            )

        if self._address is None:
            if len(addresses) == 1:
                return next(iter(addresses.values()))
            raise SourceArgumentRequiredWithSuggestions(
                "address",
                "Select the property for which to retrieve the schedule.",
                sorted(addresses),
            )

        if self._address not in addresses:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, sorted(addresses)
            )
        return addresses[self._address]

    def _get_access_token(self) -> str:
        session = requests.Session()

        response = session.get(CSRF_URL, timeout=30)
        response.raise_for_status()
        csrf_token = response.json().get("csrfToken")
        if not csrf_token:
            raise SourceArgumentExceptionMultiple(
                ("email", "password"), "Could not initialize the AEN login."
            )

        response = session.post(
            LOGIN_URL,
            data={
                "id": self._email,
                "password": self._password,
                "csrfToken": csrf_token,
                "callbackUrl": BASE_URL,
                "json": "true",
            },
            timeout=30,
        )
        response.raise_for_status()

        response = session.get(SESSION_URL, timeout=30)
        response.raise_for_status()
        access_token = response.json().get("accessToken")
        if not access_token:
            raise SourceArgumentExceptionMultiple(
                ("email", "password"), "Login failed: invalid credentials."
            )
        return access_token


def _parse_date(value: str) -> date | None:
    match = _DATE_PATTERN.match(value)
    if match is None:
        return None

    milliseconds = int(match.group(1))
    offset = match.group(2)
    if offset is None:
        return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).date()

    sign = 1 if offset.startswith("+") else -1
    hours = int(offset[1:3])
    minutes = int(offset[3:5])
    tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
    return datetime.fromtimestamp(milliseconds / 1000, tz).date()
