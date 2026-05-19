import json
from datetime import datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "South Lanarkshire Council"
DESCRIPTION = "Source for South Lanarkshire Council waste collection."
URL = "https://wasteservices.southlanarkshire.gov.uk"
COUNTRY = "uk"

DASHBOARD_URL = "https://wasteservices.southlanarkshire.gov.uk/PublicDashboard"
REQUEST_TIMEOUT = 30

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
    "1 Clincarthill Road, Glasgow, G73 2LF": {"postcode": "G73 2LF", "uprn": 484129473},
    "55 Chapel Court, Glasgow, G73 1UR": {"postcode": "G73 1UR", "uprn": 484000600},
    "Flat 1 10, Burnside Lane, Hamilton, ML3 6QP": {
        "postcode": "ML3 6QP",
        "uprn": 484073020,
    },
    "2 Braxfield Road, Lanark, ML11 9AB": {"postcode": "ML11 9AB", "uprn": 484118513},
}


class Source:
    def __init__(self, postcode: str, uprn: int):
        self._postcode = postcode.strip().upper()
        self._uprn = int(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        # Step 1: GET the dashboard to obtain the CSRF token
        resp = session.get(DASHBOARD_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_input:
            raise ValueError("Could not find CSRF token on dashboard page")
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
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        premises = self._extract_premises(resp.text)

        # Step 3: Extract the appointments JSON embedded in the response HTML
        appointments = self._extract_appointments(resp.text)
        if not appointments:
            suggestions = [
                f"{premise['Premises']} (UPRN {premise['UPRN']})"
                for premise in premises
                if isinstance(premise, dict)
                and premise.get("Premises")
                and premise.get("UPRN") is not None
            ]
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "uprn", self._uprn, suggestions
                )
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

        entries.sort(key=lambda entry: (entry.date, entry.type))
        return entries

    @staticmethod
    def _extract_appointments(html: str) -> list:
        """Extract the appointments dataSource JSON embedded in the page HTML.

        The page contains two dataSource blocks: one for the premises dropdown
        and one for the scheduler appointments. The appointments block is
        identified by containing a "Subject" key in each entry.
        """
        for data in Source._extract_data_sources(html):
            if data and isinstance(data[0], dict) and "Subject" in data[0]:
                return data
        return []

    @staticmethod
    def _extract_premises(html: str) -> list:
        for data in Source._extract_data_sources(html):
            if data and isinstance(data[0], dict) and "Premises" in data[0]:
                return data
        return []

    @staticmethod
    def _extract_data_sources(html: str) -> list:
        marker = '"dataSource": ejs.data.DataUtil.parse.isJson('
        search_from = 0
        data_sources = []
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
                if isinstance(data, list):
                    data_sources.append(data)
            except (json.JSONDecodeError, IndexError):
                pass
            search_from = idx + 1
        return data_sources
