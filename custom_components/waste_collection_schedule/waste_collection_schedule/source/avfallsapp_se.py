from datetime import datetime
import json
import logging
from uuid import uuid4

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Avfallsapp.se - Multi Source"
DESCRIPTION = "Source for all Avfallsapp waste collection sources. This included multiple municipalities in Sweden."
URL = "https://www.avfallsapp.se"
TEST_CASES = {
    "Söderköping - Söderköping Kommun": {
        "api_key": "!secret avfallsapp_se_api_key",
        "service_provider": "soderkoping",
    },
}

COUNTRY = "se"
_LOGGER = logging.getLogger(__name__)

ICON_RECYCLE = "mdi:recycle"

# See documentatation about possible other cities and service providers
# that look as using the same portal (sub-domain lookup).
SERVICE_PROVIDERS = {
    "soderkoping": {
        "title": "Söderköping",
        "url": "https://soderkoping.se",
        "api_url": "https://soderkoping.avfallsapp.se/wp-json/nova/v1/",
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
    ):
        # Raise an exception if the user did not provide akpi_key or street_address
        if not api_key and not street_address:
            raise SourceArgumentExceptionMultiple(
                ["street_address", "api_key"],
                "You must provide either a street_address or a api_key",
            )
        self._api_key = api_key
        self._street_address = street_address
        # Get the api url using the service provider
        self._url = SERVICE_PROVIDERS.get(service_provider.lower(), {}).get("api_url")
        if self._url is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "service_provider",
                service_provider,
                SERVICE_PROVIDERS.keys(),
            )
        # Remove trailing slash from the url if present
        if self._url.endswith("/"):
            self._url = self._url[:-1]

    def _register_device(self):
        if not self._street_address:  # should not happen
            raise Exception("street_address required to register device")
        uuid = uuid4().hex[:16]

        # if not self._api_key:
        registerUrl = self._url + "/register"
        params = {
            "identifier": uuid,
            "uuid": uuid,
            "platform": "android",
            "version": "2.2.0.0",
            "os_version": "14",
            "model": "sdk_gphone64_x86_64",
            "test": False,
        }
        response = requests.post(
            registerUrl, json=params, timeout=30, headers={"X-App-Identifier": uuid}
        )
        self._api_key = uuid

    def _register_address(self):
        params = {"address": self._street_address.replace(" ", "%20")}
        # Use the street address to find the full street address with the building ID
        searchUrl = self._url + "/next-pickup/search"
        # Search for the address
        response = requests.get(
            searchUrl,
            params=params,
            headers={"X-App-Identifier": self._api_key},
            timeout=30,
        )
        address_data = json.loads(response.text)
        address = None
        # Make sure the response is valid and contains data
        if address_data and len(address_data) > 0:
            addresses = [
                a for _, address_list in address_data.items() for a in address_list
            ]
            # Check if the request was successful
            for a in addresses:
                # The request can be successful but still not return any buildings at the specified address
                if a["address"].lower().replace(
                    " ", ""
                ) == self._street_address.lower().replace(" ", ""):
                    address = a
                    break
            if not address:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street_address",
                    self._street_address,
                    [a["address"] for a in addresses],
                )

        # Raise exception if all the above checks failed
        if not address:
            raise Exception(
                "street_address",
                f"Failed to find building address for: {self._street_address}",
            )

        data = {
            "plant_id": address["plant_number"],
            "address_enabled": True,
            "notification_enabled": False,
        }

        # Set the address as the active address
        response = requests.post(
            self._url + "/next-pickup/set-status",
            json=data,
            headers={"X-App-Identifier": self._api_key},
            timeout=30,
        )
        response.raise_for_status()

    def fetch(self):
        if not self._api_key:
            self._register_device()
            self._register_address()
            raise SourceArgumentRequiredWithSuggestions(
                "api_key", "Select the generated api_key from list", [self._api_key]
            )

        # Use the API key to get the waste collection schedule for registered addresses.
        getUrl = self._url + "/next-pickup/list?"
        response = requests.get(
            getUrl, headers={"X-App-Identifier": self._api_key}, timeout=30
        )
        data = json.loads(response.text)
        multi_config = False
        if len(data) > 1:
            multi_config = True
        entries = []
        for entry in data:
            address = entry.get("address")
            for bin in entry.get("bins"):
                icon = ICON_RECYCLE
                waste_type = bin.get("type")
                pickup_date = bin.get("pickup_date")
                pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                if waste_type and pickup_date:
                    if multi_config:
                        waste_type = f"{address} {waste_type}"

                    _LOGGER.debug(
                        "Adding entry for %s with next pickup %s",
                        waste_type,
                        pickup_date.strftime("%Y-%m-%d"),
                    )
                    entries.append(
                        Collection(date=pickup_date, t=waste_type, icon=icon)
                    )

        return entries
