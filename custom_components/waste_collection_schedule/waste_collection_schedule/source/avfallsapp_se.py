import logging
from datetime import datetime
from uuid import uuid4

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Avfallsapp.se - Multi Source"
DESCRIPTION = (
    "Source for all Avfallsapp waste collection sources. "
    "This includes multiple municipalities in Sweden."
)
URL = "https://www.avfallsapp.se"
COUNTRY = "se"

TEST_CASES = {
    "Söderköping - Söderköping Kommun": {
        "api_key": "!secret avfallsapp_se_api_key",
        "service_provider": "soderkoping",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "You can enter a search address in the street address field and click continue. "
        "You will see an error at the api_key input field. But you should be able to "
        "select a generated key from the dropdown and continue."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "service_provider": "Service provider",
        "api_key": "API key / device ID",
        "street_address": "Street address",
        "token": "Bearer token",
    },
    "sv": {
        "service_provider": "Tjänsteleverantör",
        "api_key": "API-nyckel / enhets-ID",
        "street_address": "Gatuadress",
        "token": "Bearer-token",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "service_provider": "Name of the Avfallsapp provider.",
        "api_key": "API key or device ID used by the mobile app.",
        "street_address": "Street address used for address lookup and registration.",
        "token": "Bearer token required by some providers.",
    },
    "sv": {
        "service_provider": "Namn på Avfallsapp-leverantören.",
        "api_key": "API-nyckel eller enhets-ID från mobilappen.",
        "street_address": "Gatuadress som används för adressökning och registrering.",
        "token": "Bearer-token som krävs av vissa leverantörer.",
    },
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    "Tunna 1": "mdi:recycle",
    "Tunna 2": "mdi:recycle",
    "Hushållsavfall": "mdi:trash-can",
    "Färgat glas": "mdi:bottle-wine",
    "Ofärgat glas": "mdi:bottle-wine-outline",
    "Metall": "mdi:nail",
    "Papper": "mdi:package",
    "Plast": "mdi:bottle-soda-classic-outline",
    "Tidning": "mdi:newspaper",
    "Deponi": "mdi:delete",
}

SERVICE_PROVIDERS = {
    "soderkoping": {
        "title": "Söderköping",
        "url": "https://soderkoping.se",
        "api_url": "https://soderkoping.avfallsapp.se/wp-json/nova/v1/",
        "supports_registration": True,
        "requires_token": False,
    },
    "motala": {
        "title": "Motala",
        "url": "https://www.motala.se/",
        "api_url": "https://motala.avfallsapp.se/wp-json/nova/v1/",
        "supports_registration": True,
        "requires_token": False,
    },
    "vanersborg": {
        "title": "Vänerborg",
        "url": "https://www.vanersborg.se/",
        "api_url": "https://vanersborg.avfallsapp.se/api/nova/v1/",
        "supports_registration": False,
        "requires_token": True,
        "app_version": "3.0.0.0",
    },
}

EXTRA_INFO = [
    {
        "title": data["title"],
        "url": data["url"],
        "default_params": {"service_provider": provider},
    }
    for provider, data in SERVICE_PROVIDERS.items()
]


class Source:
    def __init__(
        self,
        service_provider: str,
        api_key: str | None = None,
        street_address: str | None = None,
        token: str | None = None,
    ):
        if not api_key and not street_address:
            raise SourceArgumentExceptionMultiple(
                ["street_address", "api_key"],
                "You must provide either a street_address or an api_key",
            )

        self._service_provider = service_provider.lower()
        cfg = SERVICE_PROVIDERS.get(self._service_provider)
        if cfg is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "service_provider",
                service_provider,
                SERVICE_PROVIDERS.keys(),
            )

        self._api_key = api_key
        self._street_address = street_address
        self._token = token

        self._url = cfg["api_url"].rstrip("/")
        self._requires_token = cfg.get("requires_token", False)
        self._supports_registration = cfg.get("supports_registration", True)
        self._app_version = cfg.get("app_version")

        if self._requires_token and not self._api_key:
            raise SourceArgumentRequired(
                "api_key",
                "This provider requires a pre-existing device ID. "
                "Find it in the mobile app under 'Om appen'.",
            )

        if self._requires_token and not self._token:
            raise SourceArgumentRequired(
                "token",
                "This provider requires a bearer token. "
                "Find it by inspecting the mobile app's network requests.",
            )

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if self._app_version:
            headers["X-App-Version"] = self._app_version

        if self._api_key:
            headers["X-App-Identifier"] = self._api_key

        if self._requires_token and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        return headers

    def _safe_json(self, response: requests.Response):
        try:
            return response.json()
        except ValueError:
            _LOGGER.debug("Non-JSON response from %s: %s", response.url, response.text)
            return None

    def _register_device(self):
        if not self._supports_registration:
            raise SourceArgumentRequired(
                "api_key",
                "This provider requires a pre-existing device ID. "
                "Find it in the mobile app under 'Om appen'.",
            )

        if not self._street_address:
            raise SourceArgumentRequired(
                "street_address", "Street address required to register device"
            )

        device_id = uuid4().hex[:16]
        url = self._url + "/register"
        payload = {
            "identifier": device_id,
            "uuid": device_id,
            "platform": "android",
            "version": "2.2.0.0",
            "os_version": "14",
            "model": "sdk_gphone64_x86_64",
            "test": False,
        }

        response = requests.post(
            url,
            json=payload,
            timeout=30,
            headers={"X-App-Identifier": device_id},
        )

        if not response.ok:
            raise SourceArgumentException(
                "api_key",
                f"Failed to register new API key: {response.text}",
            )

        self._api_key = device_id
        _LOGGER.info("Registered new API key %s", device_id)

    def _register_address(self):
        if not self._supports_registration:
            raise SourceArgumentRequired(
                "api_key",
                "This provider requires a pre-existing device ID. "
                "Find it in the mobile app under 'Om appen'.",
            )

        if not self._street_address:
            raise SourceArgumentRequired(
                "street_address", "Street address required to register address"
            )

        params = {"address": self._street_address}
        url = self._url + "/next-pickup/search"

        response = requests.get(
            url,
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        address_data = self._safe_json(response)

        address = None
        if address_data:
            addresses = [
                item
                for _, address_list in address_data.items()
                for item in address_list
            ]

            for candidate in addresses:
                if candidate["address"].lower().replace(" ", "") == (
                    self._street_address.lower().replace(" ", "")
                ):
                    address = candidate
                    break

            if not address:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_address",
                    self._street_address,
                    [item["address"] for item in addresses],
                )

        if not address:
            raise SourceArgumentException(
                "street_address",
                f"Failed to find building address for: {self._street_address}",
            )

        payload = {
            "plant_id": address["plant_number"],
            "address_enabled": True,
            "notification_enabled": False,
        }

        response = requests.post(
            self._url + "/next-pickup/set-status",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()

        if response.ok:
            _LOGGER.info(
                "Registered new address %s with plant-id %s to API key %s",
                address["address"],
                address["plant_number"],
                self._api_key,
            )
        else:
            raise SourceArgumentException(
                "street_address",
                f"Failed to register new address: {response.text}",
            )

    def _fetch_list(self, endpoint: str):
        url = f"{self._url}/next-pickup/{endpoint}"
        response = requests.get(
            url,
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()

        data = self._safe_json(response)
        if data is None:
            return []

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            if "items" in data and isinstance(data["items"], list):
                return data["items"]

        _LOGGER.debug("Unexpected pickup payload from %s: %s", url, data)
        return []

    def fetch(self):
        if not self._api_key:
            self._register_device()
            self._register_address()
            raise SourceArgumentRequiredWithSuggestions(
                "api_key",
                "Select the generated api_key from list",
                [self._api_key],
            )

        data = self._fetch_list("list")

        if not data:
            _LOGGER.debug("No data from list, trying listV2")
            data = self._fetch_list("listV2")

        multi_config = isinstance(data, list) and len(data) > 1
        entries = []

        for entry in data:
            address = entry.get("address", "")
            bins = entry.get("bins", [])

            if not isinstance(bins, list):
                _LOGGER.debug("Skipping entry with unexpected bins payload: %s", entry)
                continue

            for waste_bin in bins:
                waste_type = waste_bin.get("type")
                pickup_date = waste_bin.get("pickup_date")

                if not waste_type or not pickup_date:
                    continue

                try:
                    pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                except ValueError:
                    _LOGGER.debug(
                        "Skipping entry with unexpected date format: %s", pickup_date
                    )
                    continue

                icon = ICON_MAP.get(waste_type, "mdi:trash-can")

                if multi_config and address:
                    waste_type = f"{address} {waste_type}"

                entries.append(
                    Collection(
                        date=pickup_date,
                        t=waste_type,
                        icon=icon,
                    )
                )

        return entries
