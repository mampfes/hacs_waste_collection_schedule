import json
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Hounslow"
DESCRIPTION = "Source for London Borough of Hounslow."
URL = "https://hounslow.gov.uk"
TEST_CASES = {
    "10090801236": {"uprn": 10090801236},
    "100021552942": {"uprn": 100021552942},
}

ICON_MAP = {
    "Residual": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food",
    "Garden": "mdi:leaf",
}

BASE_URL = "https://my.hounslow.gov.uk"
INITIAL_URL = f"{BASE_URL}/en/service/Waste_and_recycling_collections"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST = f"{BASE_URL}/apibroker/domain/my.hounslow.gov.uk"
API_URL = f"{BASE_URL}/apibroker/runLookup"

TOKEN_LOOKUP_ID = "655f4290810cf"
JOBS_LOOKUP_ID = "659eb39b66d5a"
TIMEOUT = 30


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def _init_session(self) -> str:
        self._session = requests.Session()
        r = self._session.get(INITIAL_URL, timeout=TIMEOUT)
        r.raise_for_status()
        params = {
            "uri": r.url,
            "hostname": "my.hounslow.gov.uk",
            "withCredentials": "true",
        }
        r = self._session.get(AUTH_URL, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        session_key = r.json()["auth-session"]

        params = {
            "sid": session_key,
            "_": str(int(datetime.now().timestamp() * 1000)),
        }
        r = self._session.get(AUTH_TEST, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return session_key

    def _run_lookup(self, sid: str, lookup_id: str, form_values: dict) -> dict:
        params = {
            "id": lookup_id,
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": str(int(datetime.now().timestamp() * 1000)),
            "sid": sid,
        }
        r = self._session.post(
            API_URL,
            params=params,
            json={"formValues": {"Section 1": form_values}},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def fetch(self) -> list[Collection]:
        sid = self._init_session()

        # Step 1: get Bartec auth token
        token_resp = self._run_lookup(
            sid,
            TOKEN_LOOKUP_ID,
            {"searchUPRN": {"value": self._uprn}},
        )
        rows = (
            token_resp.get("integration", {})
            .get("transformed", {})
            .get("rows_data", {})
        )
        if not rows:
            raise ValueError(f"Failed to get Bartec token for UPRN {self._uprn}")
        bartec_token = rows["0"]["bartecToken"]

        # Step 2: get collection jobs for next 6 months
        today = date.today()
        six_months = today + timedelta(days=182)
        jobs_resp = self._run_lookup(
            sid,
            JOBS_LOOKUP_ID,
            {
                "searchUPRN": {"value": self._uprn},
                "bartecToken": {"value": bartec_token},
                "searchFromDate": {"value": today.isoformat()},
                "searchToDate": {"value": six_months.isoformat()},
            },
        )

        jobs_rows = (
            jobs_resp.get("integration", {}).get("transformed", {}).get("rows_data", {})
        )
        if not jobs_rows:
            raise ValueError(f"No collection data found for UPRN {self._uprn}")

        jobs_json = jobs_rows.get("0", {}).get("jobsJSON", "[]")
        jobs = json.loads(jobs_json.strip())

        seen = set()
        entries = []
        for job in jobs:
            job_date = datetime.strptime(job["jobDate"], "%Y-%m-%d").date()
            job_type = job.get("jobType", job.get("jobName", "Unknown"))
            key = (job_date, job_type)
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                Collection(
                    date=job_date,
                    t=job_type,
                    icon=ICON_MAP.get(job_type),
                )
            )

        if not entries:
            raise ValueError(f"No collections found for UPRN {self._uprn}")
        return entries
