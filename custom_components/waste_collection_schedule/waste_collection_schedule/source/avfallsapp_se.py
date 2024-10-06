import json
import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Avfallsapp.se - Multi Source"
DESCRIPTION = "Source for all Avfallsapp waste collection sources. This included multiple municipalities in Sweden."
URL = "https://www.avfallsapp.se"
TEST_CASES = {
    # "https://edpmypage.roslagsvatten.se/FutureWebOS/SimpleWastePickup, Andromedavägen 1, Åkersberga": {
    #     "street_address": "Andromedavägen 1",
    #     "url": "https://edpmypage.roslagsvatten.se/FutureWebOS/SimpleWastePickup",
    # },
    # "Boden - Bodens Kommun": {
    #     "street_address": "KYRKGATAN 24",
    #     "service_provider": "boden",
    # },
    # "Boden - Gymnasiet": {
    #     "street_address": "IDROTTSGATAN 4",
    #     "url": "https://edpmobile.boden.se/FutureWeb/SimpleWastePickup",
    # },
    # "Uppsalavatten - Test1": {
    #     "street_address": "SADELVÄGEN 1",
    #     "url": "https://futureweb.uppsalavatten.se/Uppsala/FutureWeb/SimpleWastePickup",
    # },
    # "Uppsalavatten - Test2": {
    #     "street_address": "BJÖRKLINGE-GRÄNBY 33",
    #     "service_provider": "uppsalavatten",
    # },
    # "Uppsalavatten - Test3": {
    #     "street_address": "BJÖRKLINGE-GRÄNBY 20",
    #     "service_provider": "uppsalavatten",
    # },
    # "SSAM - Home": {
    #     "street_address": "Asteroidvägen 1, Växjö",
    #     "service_provider": "ssam",
    # },
    # "SSAM - Slambrunn": {
    #     "street_address": "Svanebro Ormesberga, Ör",
    #     "service_provider": "ssam",
    # },
    # "Skelleftea - Test1": {
    #     "street_address": "Frögatan 76 -150",
    #     "service_provider": "skelleftea",
    # },
    # "Borås - Test1": {
    #     "street_address": "Länghemsgatan 10",
    #     "service_provider": "boras",
    # },
    # "Borås - Test2": {
    #     "street_address": "Yttre Näs 1, Seglora",
    #     "service_provider": "boras",
    # },
    # "Borås - Test3": {
    #     "street_address": "Stora Hyberg 1, Brämhult",
    #     "url": "https://kundportal.borasem.se/EDPFutureWeb/SimpleWastePickup",
    # },
    # "Kretslopp Sydost Hägnevägen 1, Sävsjö": {
    #     "street_address": "Hägnevägen 1, Sävsjö",
    #     "service_provider": "kretslopp-sydost",
    # },
}

COUNTRY = "se"
_LOGGER = logging.getLogger(__name__)

# This maps the icon based on the waste type
# ICON_MAP = {
#     "Brännbart": "mdi:trash-can",
#     "Matavfall tätt": "mdi:food",
#     "Deponi": "mdi:recycle",
#     "Restavfall": "mdi:trash-can",
#     "Matavfall": "mdi:food-apple",
#     "Slam": "mdi:emoticon-poop",
#     "Trädgårdsavfall": "mdi:leaf",
# }
ICON_RECYCLE = "mdi:recycle"

# atvidaberg.avfallsapp.se
# avfallsappen.avfallsapp.se
# boras.avfallsapp.se
# dalavatten.avfallsapp.se
# finspang.avfallsapp.se
# gullspang.avfallsapp.se
# habo.avfallsapp.se
# june.avfallsapp.se
# kil.avfallsapp.se
# kinda.avfallsapp.se
# knivsta.avfallsapp.se
# kungsbacka.avfallsapp.se
# molndal.avfallsapp.se
# motala.avfallsapp.se
# munipal.avfallsapp.se
# nodava.avfallsapp.se
# nodra.avfallsapp.se
# rambo.avfallsapp.se
# sigtuna.avfallsapp.se
# soderhamn.avfallsapp.se
# sysav.avfallsapp.se
# ulricehamn.avfallsapp.se
# upplands-bro.avfallsapp.se
# vafab.avfallsapp.se
# vallentuna.avfallsapp.se
# vanersborg.avfallsapp.se

# v2.dalavatten.avfallsapp.se
# v2.june.avfallsapp.se
# v2.kungsbacka.avfallsapp.se

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
        street_address: str | None = None,
        api_key: str | None = None,
        service_provider: str | None = None,
    ):
        self._street_address = street_address
        self._api_key = api_key
        # Raise an exception if the user did not provide a service provider
        if service_provider is None:
            raise SourceArgumentExceptionMultiple(
                ["service_provider", "url"],
                "You must provide either a service provider or a url",
            )
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

    def fetch(self):
        # https://soderkoping.avfallsapp.se/wp-json/
        # if not self._api_key:
        #     registerUrl = self._url + "/register"
        #     params = {
        #         "uuid": "3546843546854136461354384",
        #         "platform": "home assistant",
        #         "version": "12",
        #         "os_version": "3",
        #         "model": "green",
        #         "test": "no",
        #     }
        #     response = requests.post(registerUrl, params=params, timeout=30)
        #     key_data = json.loads(response.text)

        # params = {"searchText": self._street_address}
        # Use the street address to find the full street address with the building ID
        # searchUrl = self._url + "/SearchAdress"
        # Search for the address
        # response = requests.post(searchUrl, params=params, timeout=30)
        # address_data = json.loads(response.text)
        # address = None
        # # Make sure the response is valid and contains data
        # if address_data and len(address_data) > 0:
        #     # Check if the request was successful
        #     if address_data["Succeeded"]:
        #         # The request can be successful but still not return any buildings at the specified address
        #         if len(address_data["Buildings"]) > 0:
        #             address = address_data["Buildings"][0]
        #         else:
        #             raise SourceArgumentException(
        #                 "street_address",
        #                 f"No returned building address for: {self._street_address}",
        #             )
        #     else:
        #         raise SourceArgumentException(
        #             "street_address",
        #             f"The server failed to fetch the building data for: {self._street_address}",
        #         )
        # # Raise exception if all the above checks failed
        # if not address:
        #     raise SourceArgumentException(
        #         "street_address",
        #         f"Failed to find building address for: {self._street_address}",
        #     )

        # # Use the API key get the waste collection schedule for registered addresses
        getUrl = self._url + "/next-pickup/list?"
        # Get the waste collection schedule
        response = requests.get(
            getUrl, headers={"X-App-Identifier": self._api_key}, timeout=30
        )
        data = json.loads(response.text)
        entries = []
        for entry in data:
            address = entry.get("address")
            # plant_id = entry.get("plant_id")
            for bin in entry.get("bins"):
                icon = ICON_RECYCLE
                waste_type = bin.get("type")
                pickup_date = bin.get("pickup_date")
                pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                if waste_type and pickup_date:
                    entries.append(
                        Collection(
                            date=pickup_date, t=f"{address} {waste_type}", icon=icon
                        )
                    )

        return entries
