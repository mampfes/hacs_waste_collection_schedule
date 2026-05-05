from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from curl_cffi import requests
from waste_collection_schedule import Collection
from waste_collection_schedule import exceptions as exc

TITLE = "Mustankorkea"
DESCRIPTION = "Schedule for Mustankorkea"
URL = "https://www.mustankorkea.fi"
TEST_CASES = {
    "CID": {
        "username": "!secret mustankorkea_fi_username",
        "password": "!secret mustankorkea_fi_password",
        "contract_id": "!secret mustankorkea_fi_contract_id",
    },
    "NoCID": {
        "username": "!secret mustankorkea_fi_username",
        "password": "!secret mustankorkea_fi_password",
    },
}
ICON_MAP = {
    "SEKA": "mdi:trash-can",
    "BIO": "mdi:leaf",
    # Unsure about these
    # "MUO": "mdi:delete-variant",
    # "KAR": "mdi:package-variant",
    # "LAS": "mdi:glass-wine",
    # "MET": "mdi:tools",
}

API_URL = "https://oma.mustankorkea.fi/api"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Create an account at oma.mustankorkea.fi to get username and password."
    'If you have more than one contract, after logging in select your contract under "Omat kohteet" and '
    "then see the last part of the URL after emptying-infos/ for the contract ID."
}

PARAM_DESCRIPTIONS = {
    "en": {
        "username": "Username for oma.mustankorkea.fi account",
        "password": "Password for oma.mustankorkea.fi account",
        "contract_id": "Waste collection contract ID, only required if you have multiple contracts",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "username": "",
        "password": "",
        "contract_id": "e.g. 30-00012345-00",
    }
}


class Source:
    REQUEST_TIMEOUT = 10

    def __init__(
        self,
        username: str,
        password: str,
        contract_id: str | None = None,
    ):
        self._username = username
        self._password = password
        self._contract_id = contract_id
        self._token = None
        self._token_expires = None

    @contextmanager
    def get_session(self):
        ses = requests.Session(impersonate="chrome124")
        try:
            if not self._token or (
                self._token_expires
                and self._token_expires
                <= (datetime.now(timezone.utc) + timedelta(minutes=2))
            ):
                try:
                    r = ses.post(
                        f"{API_URL}/customers/Users/login",
                        json={
                            "userName": self._username,
                            "password": self._password,
                        },
                        headers={
                            "Tenant-Id": "3b09f6f9-9458-40e2-9f69-e16e198d0353",
                        },
                        timeout=self.REQUEST_TIMEOUT,
                    )
                    r.raise_for_status()
                    data = r.json()
                    self._token = data["token"]
                    expires = datetime.fromisoformat(data["expiresAt"])

                    if expires.tzinfo is None:
                        expires = expires.replace(tzinfo=timezone.utc)

                    self._token_expires = expires
                except Exception as e:
                    raise exc.SourceArgumentExceptionMultiple(
                        ["username", "password"], "Failed to login, check credentials"
                    ) from e

            ses.headers.update({"Authorization": f"Vingo-e-services {self._token}"})

            if not self._contract_id:
                try:
                    r = ses.get(
                        f"{API_URL}/customers/Customers/emptying-infos",
                        timeout=self.REQUEST_TIMEOUT,
                    )
                    r.raise_for_status()
                    data = r.json()
                    if not isinstance(data, list):
                        raise TypeError(
                            f"Expected emptying-infos response to be a list, not {type(data)}"
                        )
                    if len(data) == 0:
                        raise ValueError("No contracts found")
                    if len(data) > 1:
                        raise exc.SourceArgumentRequiredWithSuggestions(
                            "contract_id",
                            "Multiple contracts found",
                            [c["id"] for c in data],
                        )
                    self._contract_id = data[0]["id"]
                except (
                    exc.SourceArgumentException,
                    exc.SourceArgumentExceptionMultiple,
                ):
                    raise
                except Exception as e:
                    raise exc.SourceArgumentException(
                        "contract_id",
                        "Failed to get contract ID, please specify it manually",
                    ) from e
            yield ses
        finally:
            ses.close()

    def fetch(self) -> list[Collection]:
        entries = []
        with self.get_session() as session:
            try:
                r = session.get(
                    f"{API_URL}/customers/Customers/emptying-infos/{self._contract_id}/contracts",
                    timeout=self.REQUEST_TIMEOUT,
                )
                r.raise_for_status()
                data = r.json()
                if not isinstance(data, list):
                    raise TypeError(
                        f"Expected contracts response to be a list, not {type(data)}"
                    )
            except Exception as e:
                raise exc.SourceArgumentException(
                    "contract_id",
                    "Failed to get collection data, please check contract ID",
                ) from e

            for contract in data:
                # Filter out contracts w/o collection date (base fees etc)
                if "nextEmptying" not in contract or not contract["nextEmptying"]:
                    continue

                # Basic info for this contract
                t = contract["name"]
                icon = ICON_MAP.get(contract["size"].split(" ")[0], "mdi:trash-can")

                try:
                    # Get full emptying schedule for this product in the contract
                    r = session.get(
                        f"{API_URL}/customers/Customers/emptying-infos/{self._contract_id}/contracts/{contract['position']}",
                        timeout=self.REQUEST_TIMEOUT,
                    )
                    r.raise_for_status()
                    details = r.json()
                    if "allEmptyings" not in details:
                        raise KeyError("No allEmptyings in response")
                    if not isinstance(details["allEmptyings"], dict):
                        raise TypeError(
                            f"Expected allEmptyings to be a dict, not {type(details['allEmptyings'])}"
                        )
                    for kind, info in details["allEmptyings"].items():
                        if not isinstance(info, list):
                            continue
                        for entry in info:
                            date = datetime.fromisoformat(entry["emptyingDate"]).date()
                            entries.append(Collection(date=date, t=t, icon=icon))
                except Exception:
                    # Full schedule not available for some reason, fall back to nextEmptying only
                    entries.append(
                        Collection(
                            date=datetime.fromisoformat(
                                contract["nextEmptying"]
                            ).date(),
                            t=t,
                            icon=icon,
                        )
                    )
        return entries
