import datetime

import requests

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "London Borough of Lambeth"
DESCRIPTION = "Source for London Borough of Lambeth"
URL = "https://www.lambeth.gov.uk/"

TEST_CASES = {
    "Sternhold Avenue": {"uprn": "100021893293"},
    "Sibella Road": {"uprn": "100021889496"},
    "Hoadly Road": {"uprn": "100021852695"},
}

API_URL = "https://wasteservice.lambeth.gov.uk/WhitespaceComms/GetServicesByUprn"

ICON_MAP = {
    "Domestic Food Collection Service": "mdi:food",
    "Domestic Recycling Collection Service": "mdi:recycle",
    "Domestic Refuse Collection Service": "mdi:trash-can",
    "Domestic Garden Collection Service": "mdi:leaf",
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Property UPRN (Unique Property Reference Number)",
    },
    "de": {
        "uprn": "UPRN der Immobilie",
    },
    "it": {
        "uprn": "UPRN della proprietà",
    },
    "fr": {
        "uprn": "UPRN du bien",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Find your UPRN at https://www.findmyaddress.co.uk/",
    },
    "de": {
        "uprn": "Finden Sie Ihre UPRN unter https://www.findmyaddress.co.uk/",
    },
    "it": {
        "uprn": "Trova il tuo UPRN su https://www.findmyaddress.co.uk/",
    },
    "fr": {
        "uprn": "Trouvez votre UPRN sur https://www.findmyaddress.co.uk/",
    },
}

# Strict allowlist of valid waste collection services
ALLOWED_SERVICES = set(ICON_MAP.keys())


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        payload = {
            "uprn": self._uprn,
            "includeEventTypes": False,
            "includeFlags": True,
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise Exception("API request timed out")
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")

        try:
            data = response.json()
        except ValueError:
            raise Exception("Invalid JSON response")

        services = data.get("SiteServices")
        if not services:
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []

        for item in services:
            service_name = item.get("ServiceDescription")
            next_date_str = item.get("NextCollectionDate")

            if not service_name or not next_date_str:
                continue

            if service_name not in ALLOWED_SERVICES:
                continue

            try:
                collection_date = datetime.datetime.strptime(
                    next_date_str, "%d/%m/%Y"
                ).date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=service_name,
                    icon=ICON_MAP.get(service_name, "mdi:trash-can"),
                )
            )

        if not entries:
            raise Exception("No valid waste collection entries found")

        return entries