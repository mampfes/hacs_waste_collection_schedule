from datetime import datetime, timedelta
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Rochdale Borough Council"
DESCRIPTION = "Source for Rochdale Borough Council, UK."
URL = "https://www.rochdale.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10094359340"},
    "Test_002": {"uprn": "23030658"},
    "Test_003": {"uprn": "23011384"},
    "Test_004": {"uprn": "23045922"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Paper and Cardboard": "mdi:recycle",
    "Glass and Bottles": "mdi:glass-fragile",
    "Food and Garden": "mdi:leaf",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)
        self._base_url = "https://rochdale-self.achieveservice.com"

    def fetch(self):
        s = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self._base_url}/service/Bins___view_your_waste_collection_calendar",
        }

        # 1. Initialize session and get SID
        ts = time_ns() // 1_000_000
        sGet = s.get(
            f"{self._base_url}/apibroker/domain/rochdale-self.achieveservice.com?_={ts}",
            headers=headers,
            timeout=30,
        )
        sGet.raise_for_status()

        auth_url = f"{self._base_url}/authapi/isauthenticated?uri=https%3A%2F%2Frochdale-self.achieveservice.com%2Fservice%2FBins___view_your_waste_collection_calendar&hostname=rochdale-self.achieveservice.com&withCredentials=true"
        sidGet = s.get(auth_url, headers=headers, timeout=30)
        sidGet.raise_for_status()

        sid = sidGet.json().get("auth-session")

        if not sid:
            raise Exception("Rochdale API: Failed to obtain a session ID.")

        # 2. STEP 1: Fetch the required Bartec Token using the UPRN
        # Lookup 6846c784a46b5 returns the server-side {bartecToken}
        payload_token = {
            "formId": "AF-Form-d7812e2d-2876-47c2-9802-8a4a3b1a2264",
            "formValues": {"Location details": {"propertyUPRN": {"value": self._uprn}}},
        }

        ts = time_ns() // 1_000_000
        token_url = f"{self._base_url}/apibroker/runLookup?id=6846c784a46b5&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={ts}&sid={sid}"
        r_token = s.post(token_url, headers=headers, json=payload_token, timeout=30)
        r_token.raise_for_status()

        # Fetch the Bartec Token
        try:
            bartec_token = r_token.json()["integration"]["transformed"]["rows_data"][
                "0"
            ]["bartecToken"]
        except KeyError:
            raise ValueError(
                f"Rochdale API: Failed to retrieve bartecToken for UPRN {self._uprn}."
            )

        # 3. STEP 2: Fetch the Calendar
        # Lookup 68b58a1364572 returns the annual calendar using the token and date bounds
        now = datetime.now()
        min_date = now.strftime("%Y-%m-%dT00:00:00")
        max_date = (now + timedelta(days=365)).strftime("%Y-%m-%dT23:59:59")

        payload_data = {
            "formId": "AF-Form-d7812e2d-2876-47c2-9802-8a4a3b1a2264",
            "formValues": {
                "Location details": {
                    "propertyUPRN": {"value": self._uprn},
                    "bartecToken": {"value": bartec_token},
                    "dateAnnualMinimum": {"value": min_date},
                    "dateAnnualMaximum": {"value": max_date},
                }
            },
        }

        ts = time_ns() // 1_000_000
        api_url = f"{self._base_url}/apibroker/runLookup?id=68b58a1364572&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={ts}&sid={sid}"
        r_data = s.post(api_url, headers=headers, json=payload_data, timeout=30)
        r_data.raise_for_status()
        data = r_data.json()

        # Fetch the Calendar
        rows_data = (
            data.get("integration", {}).get("transformed", {}).get("rows_data", {})
        )
        row = rows_data.get("0")

        if not row or "bartecAnnualBin1Type" not in row:
            raise ValueError(
                "Rochdale API: Failed to fetch calendar data or missing required fields."
            )

        entries = []
        for i in range(1, 17):
            bin_type = row.get(f"bartecAnnualBin{i}Type")
            day = row.get(f"bartecAnnualBin{i}Day")
            month = row.get(f"bartecAnnualBin{i}Month")

            if bin_type and day and month:
                try:
                    # Construct date using current year
                    date_str = f"{day} {month} {now.year}"
                    date_obj = datetime.strptime(date_str, "%d %B %Y").date()

                    # Handle year rollover if the date parsed is older than ~1 month ago
                    if date_obj < now.date() - timedelta(days=31):
                        date_obj = date_obj.replace(year=now.year + 1)

                    icon = ICON_MAP.get(bin_type, "mdi:trash-can")
                    entries.append(Collection(date=date_obj, t=bin_type, icon=icon))
                except KeyError:
                    continue

        return entries
