import datetime
import re
import time

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Gloucester City Council"
DESCRIPTION = "Source for Gloucester City Council, UK, bin collection dates."
URL = "https://www.gloucester.gov.uk"
TEST_CASES = {
    "1 Whimbrel Road": {"uprn": 200004478006},
    "10 Whimbrel Road": {"uprn": "200004478021"},
}

COUNTRY = "uk"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://gloucester-self.achieveservice.com/en/service/Bins___Check_your_bin_day "
        "and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number",
    }
}

HOSTNAME = "gloucester-self.achieveservice.com"
PROCESS_ID = "04123e92-cea3-42df-8131-ff6a2964ca47"
STAGE_ID = "3316d9fa-2c89-4ef6-ab0c-0adf1b5c0af8"
INITIAL_URL = f"https://{HOSTNAME}/AchieveForms/"
API_URL = f"https://{HOSTNAME}/apibroker/runLookup"

BIN_IDS_LOOKUP_ID = "63f72ddc8ca25"

# For each bin type, the chain is:
#   1. bin-ids lookup returns e.g. "RefuseId" for the address's UPRN
#   2. workflow lookup, keyed on that id, returns a "{Type}1" workflow token
#      (plus a human readable "{Type}_Schedule1" description)
#   3. next-date lookup, keyed on that workflow token, returns
#      "Next{Type}1DateISO"
BIN_TYPES = {
    "Refuse": {
        "id_field": "RefuseId",
        "workflow_lookup_id": "63f731d2b50d7",
        "next_lookup_id": "63ca72c70c3b1",
        "label": "Household waste (black bin)",
    },
    "Recycling": {
        "id_field": "RecyclingId",
        "workflow_lookup_id": "63f89f73018c0",
        "next_lookup_id": "63cfcf4756b5d",
        "label": "Recycling",
    },
    "Food": {
        "id_field": "FoodId",
        "workflow_lookup_id": "63f8a11714712",
        "next_lookup_id": "63cfcf8ac7877",
        "label": "Food waste",
    },
    "Garden": {
        "id_field": "GardenId",
        "workflow_lookup_id": "63f8a15776b5d",
        "next_lookup_id": "63cfcfc1c486c",
        "label": "Garden waste",
    },
}

ICON_MAP = {
    "Household waste (black bin)": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food waste": Icons.BIO_KITCHEN,
    "Garden waste": Icons.GARDEN,
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def _run_lookup(
        self, session: requests.Session, sid: str, lookup_id: str, section_fields: dict
    ) -> dict:
        timestamp = int(time.time() * 1000)
        resp = session.post(
            API_URL,
            params={
                "id": lookup_id,
                "repeat_against": "",
                "noRetry": "true",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AF-Renderer::Self",
                "_": timestamp,
                "sid": sid,
            },
            json={"formValues": {"Your waste collections": section_fields}},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("integration", {}).get("transformed", {}).get("rows_data", {})
        return rows.get("0", {})

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"user-agent": "Mozilla/5.0"})

        # Step 1: Load the AchieveForms page to obtain a session id
        r = session.get(
            INITIAL_URL,
            params={
                "mode": "fill",
                "consentMessage": "yes",
                "form_uri": (
                    f"sandbox-publish://AF-Process-{PROCESS_ID}"
                    f"/AF-Stage-{STAGE_ID}/definition.json"
                ),
                "process": "1",
                "process_uri": f"sandbox-processes://AF-Process-{PROCESS_ID}",
                "process_id": f"AF-Process-{PROCESS_ID}",
            },
            timeout=30,
        )
        r.raise_for_status()

        sid_match = re.search(r'"auth-session":"([^"]+)"', r.text)
        if not sid_match:
            raise SourceArgumentNotFound("uprn", self._uprn)
        sid = sid_match.group(1)

        # Step 2: Resolve the bin-type ids configured for this UPRN
        bins_row = self._run_lookup(
            session, sid, BIN_IDS_LOOKUP_ID, {"binUprn": {"value": self._uprn}}
        )
        if not bins_row:
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries: list[Collection] = []
        for bin_type, config in BIN_TYPES.items():
            bin_id = bins_row.get(config["id_field"])
            if not bin_id:
                continue

            # Step 3: Resolve the workflow token for this bin type
            workflow_row = self._run_lookup(
                session,
                sid,
                config["workflow_lookup_id"],
                {config["id_field"]: {"value": bin_id}},
            )
            workflow_id = workflow_row.get(f"{bin_type}1")
            if not workflow_id:
                continue

            # Step 4: Resolve the next collection date for this workflow
            next_row = self._run_lookup(
                session,
                sid,
                config["next_lookup_id"],
                {f"{bin_type}1": {"value": workflow_id}},
            )
            date_iso = next_row.get(f"Next{bin_type}1DateISO")
            if not date_iso:
                continue

            try:
                collection_date = datetime.datetime.strptime(
                    date_iso, "%Y-%m-%d"
                ).date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=config["label"],
                    icon=ICON_MAP.get(config["label"]),
                )
            )

        if not entries:
            raise SourceArgumentNotFound("uprn", self._uprn)

        return entries
