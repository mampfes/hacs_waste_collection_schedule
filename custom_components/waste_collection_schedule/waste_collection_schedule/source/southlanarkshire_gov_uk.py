import json
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "South Lanarkshire Council"
DESCRIPTION = "Source for South Lanarkshire Council waste collection."
URL = "https://wasteservices.southlanarkshire.gov.uk"
COUNTRY = "uk"

DASHBOARD_URL = "https://wasteservices.southlanarkshire.gov.uk/PublicDashboard"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://wasteservices.southlanarkshire.gov.uk, enter your full postcode, "
        "then select your property from the dropdown. Your UPRN is the numeric value "
        "shown in the property dropdown option — right-click the dropdown, choose "
        "Inspect Element, and look at the value= attribute of the selected <option> tag."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "uprn": "UPRN",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your full UK postcode (e.g. G73 1UR).",
        "uprn": "Unique Property Reference Number for your address (e.g. 484000600).",
    }
}

TEST_CASES = {
    "Rutherglen": {"postcode": "G73 1UR", "uprn": 484000600},
    "Hamilton": {"postcode": "ML3 6QP", "uprn": 484073020},
    "Lanark": {"postcode": "ML11 9AB", "uprn": 484118513},
}


class Source:
    def __init__(self, postcode: str, uprn: int):
        self._postcode = postcode.strip().upper()
        self._uprn = int(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        # Step 1: GET the dashboard to obtain the CSRF token
        resp = session.get(DASHBOARD_URL)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_input:
            raise RuntimeError("Could not find CSRF token on dashboard page")
        token = token_input["value"]

        # Step 2: POST to SelectPrem to retrieve the collection schedule
        resp = session.post(
            DASHBOARD_URL,
            params={"handler": "SelectPrem"},
            data={
                "SelectedPostcode": self._postcode,
                "SelectedPremises": str(self._uprn),
                "__RequestVerificationToken": token,
            },
        )
        resp.raise_for_status()

        # Step 3: Extract the appointments JSON embedded in the response HTML
        appointments = self._extract_appointments(resp.text)
        if not appointments:
            raise SourceArgumentNotFound("uprn", self._uprn)

        seen: set[tuple] = set()
        entries: list[Collection] = []
        for appt in appointments:
            try:
                date = datetime.fromisoformat(appt["StartTime"]).date()
                subject = appt["Subject"]
            except (KeyError, ValueError):
                continue
            key = (date, subject)
            if key not in seen:
                seen.add(key)
                entries.append(Collection(date=date, t=subject))

        return entries

    @staticmethod
    def _extract_appointments(html: str) -> list:
        """Extract the appointments dataSource JSON embedded in the page HTML.

        The page contains two dataSource blocks: one for the premises dropdown
        and one for the scheduler appointments. The appointments block is
        identified by containing a "Subject" key in each entry.
        """
        marker = '"dataSource": ejs.data.DataUtil.parse.isJson('
        search_from = 0
        while True:
            idx = html.find(marker, search_from)
            if idx == -1:
                break
            start = idx + len(marker)
            depth = 0
            end = start
            for i in range(start, len(html)):
                if html[i] == "[":
                    depth += 1
                elif html[i] == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            try:
                data = json.loads(html[start:end])
                if data and isinstance(data[0], dict) and "Subject" in data[0]:
                    return data
            except (json.JSONDecodeError, IndexError):
                pass
            search_from = idx + 1
        return []
