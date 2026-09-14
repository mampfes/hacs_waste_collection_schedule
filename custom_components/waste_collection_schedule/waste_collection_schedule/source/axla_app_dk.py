import logging
import random
import re
import json
from datetime import date, datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Axla Apps"
DESCRIPTION = "Support for Axlas Affaldonline Apps"
COUNTRY = "dk"
URL = "https://affaldonline.dk"
API_URL = "https://www.affaldonline.dk/api/address/collections?groupBy=date&addressId={addressid}"

ICON_MAP = {   # Optional: Dict of waste types mapped to canonical Icons
    "Rest/Mad": Icons.GENERAL_WASTE,
    "Mad/Rest": Icons.GENERAL_WASTE,
    "PMDK": Icons.PLASTIC_PACKAGING,
    "PPGM": Icons.RECYCLING,
    "Papir/Pap/Glas": Icons.RECYCLING,
    "Plast/Drikkekarton/Metal": Icons.PLASTIC_PACKAGING
}

TYPE_MAP = {
    "Mad/Rest": "Rest og Mad affald",
    "Rest/Mad": "Rest og Mad affald",
    "PMDK": "Plast og Drikkekartoner",
    "PPGM": "Pap/Papir og Glas/Metal"
}

SOURCE_CODEOWNERS = ["@superrob"]

_LOGGER = logging.getLogger("waste_collection_schedule.axla_app_dk")

AFFALDONLINE_MUNICIPALITIES = {
    "aeroe": {
        "title": "Ærø Kommune (App)",
        "url": "https://www.aeroekommune.dk/",
        "addressid": "448776",
        "client": "db765a2f-3f50-4abd-a738-3825813fedcb"
    },
    "assens": {
        "title": "Assens Forsyning (App)",
        "url": "https://www.assensforsyning.dk/",
        "addressid": "430000",
        "client": "afd912a2-44b3-402f-9e13-5aeb701ce143"
    },
    "favrskov": {
        "title": "Favrskov Forsyning (App)",
        "url": "https://www.favrskovforsyning.dk",
        "addressid": "108156",
        "client": "dffcc5b6-b9ee-478d-82e2-030123485f7e"
    },
    "ffv": {
        "title": "Faaborg Forsynings Virksomhed (App)",
        "url": "https://www.ffv.dk/",
        "addressid": "576846",
        "client": "ceca5978-6380-4ff8-ac28-9b6505457da8"
    },
    "holbaek": {
        "title": "Fors (Holbæk) (App)",
        "url": "https://www.fors.dk/",
        "addressid": "1185662",
        "client": "017efd06-ac42-4b36-8a70-ab309162e988"
    },
    "langeland": {
        "title": "Langeland Forsyning (App)",
        "url": "https://www.langeland-forsyning.dk/",
        "addressid": "383566",
        "client": "be8a9420-a9ae-42e6-83f2-eda5ec3fa29f"
    },
    "morsoe": {
        "title": "Morsø Kommune (App)",
        "url": "https://mors.dk/",
        "addressid": "1721752",
        "client": "0199b7d2-bbae-46a5-a726-293c9236f4e5"
    },
    "rebild": {
        "title": "Rebild Kommune (App)",
        "url": "https://rebild.dk/",
        "addressid": "19222886",
        "client": "cb3ddc8c-900a-43ce-ac88-ec7587db4db3"
    },
    "vejle": {
        "title": "Vejle Kommune (App)",
        "url": "https://www.vejle.dk/",
        "addressid": "1058761",
        "client": "209cb669-e2e8-4c9b-8048-8287db51a61e"
    },
    "viborg": {
        "title": "Revas (Viborg Kommune) (App)",
        "url": "https://www.revas.dk/",
        "addressid": "8739",
        "client": "4EBB900C-088E-475F-83ED-B087F4AD07BA"
    },
}

EXTRA_INFO = [
    {
        "title": info["title"],
        "url": info["url"],
        "default_params": {"municipality": municipality},
    }
    for municipality, info in AFFALDONLINE_MUNICIPALITIES.items()
]


def select_test_cases(municipalities):
    test_cases = {}
    for name, info in municipalities.items():
        test_cases[name] = {
            "municipality": name,
            "addressid": info["addressid"]
        }

    return test_cases


# Dynamically generate TEST_CASES from the AFFALDONLINE_MUNICIPALITIES dictionary
TEST_CASES = select_test_cases(
    AFFALDONLINE_MUNICIPALITIES
)

class Source:
    def __init__(self, municipality: str, addressid: str):
        _LOGGER.debug(
            "Initializing Source with municipality=%s, addressid=%s", municipality, addressid
        )
        self._api_url = API_URL.format(addressid=addressid)
        self._client_provider = AFFALDONLINE_MUNICIPALITIES.get(municipality, {}).get(
            "client", ""
        )
        if self._client_provider == "":
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, AFFALDONLINE_MUNICIPALITIES.keys()
            )
        self._client_provider = str(self._client_provider)

    def fetch(self) -> list[Collection]:
        _LOGGER.debug("Fetching data from %s", self._api_url)

        entries: list[Collection] = []
        response = requests.get(self._api_url, headers={
            "X-Client-Provider": self._client_provider,
            "X-Client-Type": "Kunde app",
            "X-Client-OS": "android",
            "X-Client-Version": "9999" # Needs to be higher than the current version.
        })
        response.raise_for_status()

        json_content = json.loads(response.text)
        if "message" in json_content:
            raise ValueError(
            "Error from API: " + json_content["message"]
        )

        for entry in json_content:
            for collection in entry["collections"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            entry["date"], "%Y-%m-%d"
                        ).date(),
                        t=str(TYPE_MAP.get(collection["fraction"]["name"], collection["fraction"]["name"])),
                        icon=ICON_MAP.get(collection["fraction"]["name"], Icons.GENERAL_WASTE)
                    )
                )

        return entries