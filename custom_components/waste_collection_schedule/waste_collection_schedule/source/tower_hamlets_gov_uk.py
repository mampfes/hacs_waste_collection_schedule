import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "London Borough of Tower Hamlets"
DESCRIPTION = "Source for London Borough of Tower Hamlets"
URL = "https://www.towerhamlets.gov.uk/"

TEST_CASES = {
    "Celtic St": {"uprn": "6085613"},
    "Ernest St": {"uprn": "6034631"},
    "Blue Anchor Yard": {"uprn": "6007545"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food/Garden Waste": "mdi:leaf",
    "Food Waste": "mdi:food-apple",
    "Garden Waste": "mdi:flower",
}

PARAM_TRANSLATIONS = {
    "en": {"uprn": "Property UPRN (Unique Property Reference Number)"},
    "de": {"uprn": "UPRN der Immobilie"},
    "it": {"uprn": "UPRN della proprietà"},
    "fr": {"uprn": "UPRN du bien"},
}

PARAM_DESCRIPTIONS = {
    "en": {"uprn": "Find your UPRN at https://www.findmyaddress.co.uk/"},
    "de": {"uprn": "Finden Sie Ihre UPRN unter https://www.findmyaddress.co.uk/"},
    "it": {"uprn": "Trova il tuo UPRN su https://www.findmyaddress.co.uk/"},
    "fr": {"uprn": "Trovez votre UPRN sur https://www.findmyaddress.co.uk/"},
}

ALLOWED_SERVICES = set(ICON_MAP.keys())

# Internal service IDs for the AchieveService platform
LOOKUP_ID = "654ba9e6a9886"
FORM_ID = "AF-Form-968b261c-ffa8-4368-9f00-5fe7e879d5b9"
STAGE_ID = "AF-Stage-4c6e80ac-7dc2-46e4-afa6-fd46d11565ec"


class Source:
    def __init__(self, uprn: str):
        if not uprn:
            raise SourceArgumentNotFound("uprn")
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        with requests.Session() as session:
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                }
            )

            # 1. Initialize session and perform the authentication handshake
            try:
                session.get(f"{URL}service/Find_your_waste_collection_days", timeout=30)

                auth_resp = session.get(
                    "https://towerhamlets-self.achieveservice.com/authapi/isauthenticated",
                    timeout=30,
                )
                auth_resp.raise_for_status()
                sid = auth_resp.json().get("auth-session")

                token_resp = session.get(
                    "https://towerhamlets-self.achieveservice.com/api/nextref",
                    params={"sid": sid},
                    timeout=30,
                )
                token_resp.raise_for_status()
                csrf = token_resp.json()["data"]["csrfToken"]
            except (requests.RequestException, ValueError, KeyError) as e:
                raise Exception(
                    f"Failed to authenticate with Tower Hamlets API: {e}"
                ) from e

            # 2. Construct the nested payload
            now_str = datetime.datetime.now().strftime("%Y-%m-%d")
            payload = {
                "stopOnFailure": True,
                "usePHPIntegrations": True,
                "stage_id": STAGE_ID,
                "stage_name": "Stage 1",
                "formId": FORM_ID,
                "formValues": {
                    "Section 2": {
                        "howCheck": {"value": "property"},
                        "NextCollectionFromDate": {"value": now_str},
                        "addressDetails": {
                            "value": {"Section 1": {"Address": {"value": self._uprn}}}
                        },
                        "AccountSiteUPRN": {"value": self._uprn},
                        "TH_uprn": {"value": self._uprn},
                    }
                },
            }

            # 3. Execute the lookup request
            try:
                resp = session.post(
                    "https://towerhamlets-self.achieveservice.com/apibroker/runLookup",
                    params={
                        "id": LOOKUP_ID,
                        "sid": sid,
                        "noRetry": "false",
                        "app_name": "AF-Renderer::Self",
                    },
                    json=payload,
                    headers={"X-CSRF-Token": csrf},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
            except (requests.RequestException, ValueError) as e:
                raise Exception(f"API request failed: {e}") from e

        # 4. Parse the results
        integration = data.get("integration", {}).get("transformed", {})

        # Check for explicit API error messages first
        if integration.get("error"):
            raise Exception(f"Council API Error: {integration.get('error')}")

        rows_data = integration.get("rows_data", {})
        rows = rows_data.values() if isinstance(rows_data, dict) else rows_data

        if not rows:
            return []

        entries = []
        current_date = datetime.date.today()

        for row in rows:
            service_name = row.get("CollectionService")
            date_str = row.get("CollectionDate")

            if not service_name or not date_str or service_name not in ALLOWED_SERVICES:
                continue

            try:
                full_date_str = f"{date_str} {current_date.year}"
                collection_date = datetime.datetime.strptime(
                    full_date_str, "%d %B %Y"
                ).date()

                # Year-wrap logic: if the date is in the past, it's for next year
                if collection_date < current_date - datetime.timedelta(days=7):
                    collection_date = collection_date.replace(
                        year=current_date.year + 1
                    )
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=service_name,
                    icon=ICON_MAP.get(service_name),
                )
            )

        return entries
