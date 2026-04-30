import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "London Borough of Hackney"
DESCRIPTION = "Source for London Borough of Hackney Council waste collection."
URL = "https://www.hackney.gov.uk/"

TEST_CASES = {
    "Middleton Road": {"uprn": "100021058914", "postcode": "E8 4LL"},
    "Elrington Road": {"uprn": "100021039326", "postcode": "E8 3BJ"},
    "King Edwards Road": {"uprn": "100021051283", "postcode": "E9 7SL"},
}

KEYWORD_MAP = {
    "recycling": ("Recycling", "mdi:recycle"),
    "food": ("Food Waste", "mdi:food"),
    "garden": ("Garden Waste", "mdi:leaf"),
    "gw_": ("Garden Waste", "mdi:leaf"),
    "180ltr": ("Refuse", "mdi:trash-can"),
    "240ltr": ("Refuse", "mdi:trash-can"),
    "wheeled bin": ("Refuse", "mdi:trash-can"),
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Property UPRN (Unique Property Reference Number)",
        "postcode": "Postcode",
    },
    "de": {"uprn": "UPRN der Immobilie", "postcode": "Postleitzahl"},
    "it": {"uprn": "UPRN della proprietà", "postcode": "Codice postale"},
    "fr": {"uprn": "UPRN du bien", "postcode": "Code postal"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Find your UPRN at https://www.findmyaddress.co.uk/",
        "postcode": "Postcode of the property",
    },
}

TENANT_ID = "f806d91c-e133-43a6-ba9a-c0ae4f4cccf6"
API_ROOT = f"https://waste-api-hackney-live.ieg4.net/{TENANT_ID}"
API_BASE = f"{API_ROOT}/alloywastepages"


class Source:
    def __init__(self, uprn: str, postcode: str):
        if not uprn:
            raise SourceArgumentException("uprn", "UPRN must not be empty")
        if not postcode:
            raise SourceArgumentException("postcode", "Postcode must not be empty")
        self._uprn = str(uprn).strip()
        self._postcode = str(postcode).strip().upper()

    def fetch(self) -> list[Collection]:
        with requests.Session() as session:
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": "https://hackney-waste-pages.azurewebsites.net",
                    "Referer": "https://hackney-waste-pages.azurewebsites.net/",
                }
            )

            payload = {
                "Postcode": self._postcode,
                "Filters": [
                    {
                        "Filter": "attributes_premisesBlpuClass",
                        "Include": True,
                        "StringMatch": "Prefix",
                        "Value": "R",
                    }
                ],
            }

            resp = session.post(
                f"{API_ROOT}/property/opensearch", json=payload, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()

            address_list = data.get("addressSummaries", [])
            system_id = None
            for item in address_list:
                if isinstance(item, dict) and str(item.get("uprn")) == self._uprn:
                    system_id = item.get("systemId")
                    break

            if not system_id:
                raise SourceArgumentNotFound("uprn", self._uprn)

            prop_resp = session.get(f"{API_BASE}/getproperty/{system_id}", timeout=30)
            prop_resp.raise_for_status()
            prop_data = prop_resp.json()

            container_attr = prop_data.get("providerSpecificFields", {}).get(
                "attributes_wasteContainersAssignableWasteContainers", ""
            )

            if not container_attr:
                return []

            container_ids = [c.strip() for c in container_attr.split(",") if c.strip()]
            entries = []

            for c_id in container_ids:
                try:
                    bin_data = session.get(
                        f"{API_BASE}/getbin/{c_id}", timeout=30
                    ).json()
                    raw_name = bin_data.get("subTitle", "Waste")

                    workflow_data = session.get(
                        f"{API_BASE}/getcollection/{c_id}", timeout=30
                    ).json()
                    workflow_ids = workflow_data.get("scheduleCodeWorkflowIDs", [])

                    for w_id in workflow_ids:
                        dates_resp = session.get(
                            f"{API_BASE}/getworkflow/{w_id}", timeout=30
                        )
                        dates_json = dates_resp.json()

                        raw_dates = []
                        if isinstance(dates_json, dict):
                            raw_dates = dates_json.get("trigger", {}).get("dates", [])

                        for date_str in raw_dates:
                            try:
                                date_obj = datetime.datetime.strptime(
                                    date_str.split("T")[0], "%Y-%m-%d"
                                ).date()

                                if date_obj >= datetime.date.today():
                                    display_name = raw_name
                                    icon = None

                                    for keyword, (
                                        friendly,
                                        icon_slug,
                                    ) in KEYWORD_MAP.items():
                                        if keyword in raw_name.lower():
                                            display_name = friendly
                                            icon = icon_slug
                                            break

                                    entries.append(
                                        Collection(
                                            date=date_obj,
                                            t=display_name,
                                            icon=icon,
                                        )
                                    )
                            except (ValueError, TypeError, IndexError):
                                continue
                except Exception:
                    continue

            return entries
