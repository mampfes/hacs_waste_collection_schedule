import base64
import datetime
import json
import re
import urllib.parse

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
    "fr": {"uprn": "Trouvez votre UPRN sur https://www.findmyaddress.co.uk/"},
}

ALLOWED_SERVICES = set(ICON_MAP.keys())

# Fallback IDs based on the Feb '26 version of the waste collection form
FALLBACK_LOOKUP = "654ba9e6a9886"
FALLBACK_FORM = "AF-Form-968b261c-ffa8-4368-9f00-5fe7e879d5b9"
FALLBACK_STAGE = "AF-Stage-4c6e80ac-7dc2-46e4-afa6-fd46d11565ec"


class Source:
    def __init__(self, uprn: str):
        if not uprn:
            raise SourceArgumentNotFound("uprn")
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        with requests.Session() as session:
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,image/apng,*/*;q=0.8",
                }
            )

            base_url = "https://towerhamlets-self.achieveservice.com"
            service_path = "/service/Check_your_waste_and_recycling_collection_days"

            # 1: Extracting sid and form URI in initial handshake
            response = session.get(f"{base_url}{service_path}", timeout=30)
            html_content = response.text

            sid_match = re.search(
                r'["\']auth-session["\']\s*:\s*["\']([^"\']+)["\']', html_content
            )
            uri_match = re.search(
                r'["\']publish-uri["\']\s*:\s*["\']([^"\']+)["\']', html_content
            )

            if not sid_match or not uri_match:
                raise ValueError(
                    "Handshake failed: Could not find auth-session or publish-uri."
                )

            sid = sid_match.group(1)
            stage_uri = urllib.parse.unquote(uri_match.group(1)).replace("\\/", "/")

            # 2: Extracting form metadata and dynamic lookup ID
            try:
                stage_resp = session.get(
                    f"{base_url}/api/get-document/json",
                    params={"uri": stage_uri, "sid": sid},
                )
                stage_resp.raise_for_status()
                stage_data = stage_resp.json()

                metadata = {
                    m["Name"]: m["Value"]
                    for m in stage_data.get("data", {}).get("metadata", [])
                }
                form_id = metadata.get("form-id", FALLBACK_FORM)
                stage_id = metadata.get("stage-id", FALLBACK_STAGE)

                encoded_content = stage_data.get("data", {}).get("content", "")
                decoded_content = json.loads(
                    base64.b64decode(encoded_content).decode("utf-8")
                )

                lookup_id = None
                for section in decoded_content.get("sections", []):
                    for field in section.get("fields", []):
                        if field.get("props", {}).get("dataName") == "collectionDates":
                            lookup_id = field.get("props", {}).get("lookup")
                            break
                lookup_id = lookup_id or FALLBACK_LOOKUP
            except (
                requests.RequestException,
                ValueError,
                KeyError,
                json.JSONDecodeError,
            ):
                form_id, stage_id, lookup_id = (
                    FALLBACK_FORM,
                    FALLBACK_STAGE,
                    FALLBACK_LOOKUP,
                )

            # 3: Extracting CSRF token
            token_resp = session.get(
                f"{base_url}/api/nextref", params={"sid": sid}, timeout=30
            )
            token_resp.raise_for_status()
            csrf = token_resp.json()["data"]["csrfToken"]

            # 4: Collections request
            now_str = datetime.datetime.now().strftime("%Y-%m-%d")
            payload = {
                "stopOnFailure": True,
                "usePHPIntegrations": True,
                "stage_id": stage_id,
                "stage_name": "Stage 1",
                "formId": form_id,
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

            resp = session.post(
                f"{base_url}/apibroker/runLookup",
                params={
                    "id": lookup_id,
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

        # 5: Parsing response, handling end of year-wrap if necessary
        integration = data.get("integration", {}).get("transformed", {})
        if integration.get("error"):
            raise ValueError(f"Council API Error: {integration.get('error')}")

        rows_data = integration.get("rows_data", {})
        rows = rows_data.values() if isinstance(rows_data, dict) else rows_data
        if not rows:
            return []

        entries = []
        today = datetime.date.today()
        for row in rows:
            service = row.get("CollectionService")
            date_str = row.get("CollectionDate")
            if not service or not date_str or service not in ALLOWED_SERVICES:
                continue
            try:
                dt = datetime.datetime.strptime(
                    f"{date_str} {today.year}", "%d %B %Y"
                ).date()
                if dt < today - datetime.timedelta(days=31):
                    dt = dt.replace(year=today.year + 1)
                entries.append(
                    Collection(date=dt, t=service, icon=ICON_MAP.get(service))
                )
            except ValueError:
                continue

        return entries
