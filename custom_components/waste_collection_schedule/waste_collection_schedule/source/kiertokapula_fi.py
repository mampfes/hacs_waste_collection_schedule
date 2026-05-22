import logging
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Kiertokapula Finland"
DESCRIPTION = "Schedule for Kiertokapula Finland waste collection"
URL = "https://www.kiertokapula.fi"
COUNTRY = "fi"
TEST_CASES = {
    "Test1": {
        "username": "!secret kiertokapula_fi_username",
        "password": "!secret kiertokapula_fi_password",
    }
}

API_URL = "https://asiakasnetti.kiertokapula.fi/api/customers"
TENANT_ID = "493c3a57-70d8-4515-aa94-05dd1185b986"

PARAM_TRANSLATIONS = {
    "en": {"username": "Username", "password": "Password"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "username": "Your Kiertokapula e-services username (previously the bill/customer number)",
        "password": "Your Kiertokapula e-services password",
    }
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, username: str = "", password: str = "", bill_number: str = ""):
        # Accept bill_number as a backward-compatible alias for username
        self._username = username or bill_number
        self._password = password

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Authenticate against new Vingo 2.0 API
        login_headers = {
            "Content-Type": "application/json;charset=utf-8",
            "Accept-Language": "fi",
            "Tenant-Id": TENANT_ID,
        }
        r = session.post(
            f"{API_URL}/Users/login",
            json={"userName": self._username, "password": self._password},
            headers=login_headers,
        )
        r.raise_for_status()
        token_data = r.json()
        token = token_data["token"]

        # All subsequent requests use the Vingo bearer token
        auth_headers = {
            "Content-Type": "application/json;charset=utf-8",
            "Accept-Language": "fi",
            "Authorization": f"Vingo-e-services {token}",
        }

        # Get all emptying locations for the account
        r = session.get(
            f"{API_URL}/Customers/emptying-infos",
            headers=auth_headers,
        )
        r.raise_for_status()
        emptying_infos = r.json() or []

        entries: list[Collection] = []

        for info in emptying_infos:
            emptying_id = info.get("id")
            if not emptying_id:
                continue

            # Get active contracts for this emptying location
            r = session.get(
                f"{API_URL}/Customers/emptying-infos/{emptying_id}/contracts",
                headers=auth_headers,
            )
            r.raise_for_status()
            contracts = r.json() or []

            today = date.today()
            for contract in contracts:
                # Filter to active contracts (status Unspecified or Approved, not expired)
                status = contract.get("status", "")
                if status not in ("Unspecified", "Approved"):
                    continue
                end_date_str = contract.get("endDate")
                if end_date_str:
                    try:
                        end_date = datetime.fromisoformat(end_date_str).date()
                        if end_date <= today:
                            continue
                    except (ValueError, TypeError):
                        pass

                next_emptying_str = contract.get("nextEmptying")
                if not next_emptying_str:
                    continue

                try:
                    next_emptying = datetime.fromisoformat(next_emptying_str).date()
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Could not parse nextEmptying date: %s", next_emptying_str
                    )
                    continue

                waste_type = contract.get("name") or "Waste"
                entries.append(Collection(date=next_emptying, t=waste_type))

        return entries
