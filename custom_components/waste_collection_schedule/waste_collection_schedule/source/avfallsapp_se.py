from datetime import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Avfallsapp.se - Multi Source"
DESCRIPTION = "Source for all Avfallsapp waste collection sources. This included multiple municipalities in Sweden."
URL = "https://www.avfallsapp.se"
TEST_CASES = {
    "Söderköping - Söderköping Kommun": {
        "api_key": "12345678",
        "service_provider": "soggderkoping",
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
        api_key: str,
        service_provider: str,
    ):
        self._api_key = api_key
        # Raise an exception if the user did not provide a service provider
        if service_provider is None:
            raise SourceArgumentExceptionMultiple(
                ["service_provider", "url"],
                "You must provide either a service provider or a url",
            )
        # Get the api url using the service provider
        self._url = SERVICE_PROVIDERS.get(
            service_provider.lower(), {}).get("api_url")
        if self._url is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "service_provider",
                service_provider,
                SERVICE_PROVIDERS.keys(),
            )
        # Remove trailing slash from the url if present
        if self._url.endswith("/"):
            self._url = self._url[:-1]

    def fetch(self):
        # Use the API key from phone-app to get the waste collection
        # schedule for registered addresses in app.
        getUrl = self._url + "/next-pickup/list?"
        response = requests.get(
            getUrl, headers={"X-App-Identifier": self._api_key}, timeout=30
        )
        data = json.loads(response.text)
        entries = []
        for entry in data:
            address = entry.get("address")
            for bin in entry.get("bins"):
                icon = ICON_RECYCLE
                waste_type = bin.get("type")
                waste_type_full = f"{address} {waste_type}"
                pickup_date = bin.get("pickup_date")
                pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                if waste_type and pickup_date:
                    _LOGGER.debug(
                        "Adding entry for %s with next pickup %s",
                        waste_type_full,
                        pickup_date.strftime("%Y-%m-%d"),
                    )
                    entries.append(
                        Collection(date=pickup_date,
                                   t=waste_type_full, icon=icon)
                    )

        return entries
