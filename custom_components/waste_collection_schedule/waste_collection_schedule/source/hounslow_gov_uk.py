import json
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

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

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        sid = init_session(
            session,
            INITIAL_URL,
            AUTH_URL,
            "my.hounslow.gov.uk",
            auth_test_url=AUTH_TEST,
            timeout=TIMEOUT,
        )

        # Step 1: get Bartec auth token
        token_resp = run_lookup(
            session,
            API_URL,
            sid,
            TOKEN_LOOKUP_ID,
            {"Section 1": {"searchUPRN": {"value": self._uprn}}},
            timeout=TIMEOUT,
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
        jobs_resp = run_lookup(
            session,
            API_URL,
            sid,
            JOBS_LOOKUP_ID,
            {
                "Section 1": {
                    "searchUPRN": {"value": self._uprn},
                    "bartecToken": {"value": bartec_token},
                    "searchFromDate": {"value": today.isoformat()},
                    "searchToDate": {"value": six_months.isoformat()},
                }
            },
            timeout=TIMEOUT,
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
