import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired

TITLE = "Fylde Council"
DESCRIPTION = "Source for waste.fylde.gov.uk services for Fylde Council, UK."
URL = "https://waste.fylde.gov.uk"
LOGIN_URL = f"{URL}/Identity/Account/Login"

TEST_CASES = {
    "Test1": {
        "email": "!secret fylde_gov_uk_email",
        "password": "!secret fylde_gov_uk_password",
    },
    "Test2": {
        "email": "!secret fylde_gov_uk_email",
        "password": "!secret fylde_gov_uk_password",
        "uprn": "!secret fylde_gov_uk_uprn",
    },
}

REGEX_BIN_TYPE = r"(?i)(?P<bin_type>(?:GREY|GREEN|BROWN|BLUE)\s+(?:BIN|BAG|BOX))"
ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Green Bin": "mdi:leaf",
    "Brown Bin": "mdi:recycle",
    "Blue Bin": "mdi:recycle",
    "Blue Bag": "mdi:recycle",
    "Green Box": "mdi:recycle",
}

# ### Arguments affecting the configuration GUI ####
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Register at https://waste.fylde.gov.uk/ and add your property to your account using your UPRN.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "email": "Email address for waste portal account",
        "password": "Password for waste portal account",
        "uprn": "Property UPRN (optional, only needed if you have multiple properties registered)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "email": "Email Address",
        "password": "Password",
        "uprn": "UPRN (Optional)",
    },
}

# ### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, email: str, password: str, uprn: str | int | None = None):
        if not email:
            raise SourceArgumentRequired(
                argument="email",
                reason="Email is required to authenticate with the waste portal.",
            )
        if not password:
            raise SourceArgumentRequired(
                argument="password",
                reason="Password is required to authenticate with the waste portal.",
            )

        self._email: str = email
        self._password: str = password
        self._uprn: str | int | None = uprn

    def _login(self, session: requests.Session) -> None:
        """Authenticate with the waste portal and establish a session."""
        # Get the login page to retrieve the anti-forgery token
        response = session.get(LOGIN_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})

        if not token_input:
            raise Exception("Unable to find anti-forgery token on login page")

        verification_token = token_input.get("value")
        if not verification_token:
            raise Exception("Anti-forgery token is empty")

        # Perform login
        login_data = {
            "Input.Email": self._email,
            "Input.Password": self._password,
            "__RequestVerificationToken": verification_token,
            "Input.RememberMe": "false",
        }

        response = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        response.raise_for_status()

        # Check if login was successful
        if "validation-summary-errors" in response.text or "/Identity/Account/Login" in response.url:
            raise Exception(
                "Login failed. Please check your email and password credentials."
            )

    def _extract_schedule_data(self, html: str) -> list:
        """Extract the Syncfusion Schedule data from embedded JavaScript in the HTML."""
        # Look for the Syncfusion Schedule initialisation with eventSettings.dataSource
        pattern = r"new\s+ejs\.schedule\.Schedule\s*\(\s*\{[^}]*\"eventSettings\"\s*:\s*\{\s*\"dataSource\"\s*:\s*ejs\.data\.DataUtil\.parse\.isJson\s*\(\s*(\[.*?\])\s*\)"

        match = re.search(pattern, html, re.DOTALL)
        if not match:
            raise Exception(
                "Unable to find collection schedule data in the portal page. "
                "Please ensure your account has at least one property registered."
            )

        json_data = match.group(1)

        try:
            events = json.loads(json_data)
            return events
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse collection schedule data: {e}")

    def fetch(self) -> list[Collection]:
        """Fetch waste collection schedule from the Fylde waste portal."""
        session = requests.Session()

        # Authenticate with the portal
        self._login(session)

        # Fetch the main portal page with the authenticated session
        response = session.get(URL)
        response.raise_for_status()

        # Extract the schedule data from embedded JavaScript
        events = self._extract_schedule_data(response.text)

        if not events:
            raise Exception(
                "No collection events found. Please ensure your property is registered on the waste portal."
            )

        entries = []
        for event in events:
            # Filter by UPRN if specified
            if self._uprn is not None:
                event_uprn = event.get("UPRN")
                if event_uprn != self._uprn and str(event_uprn) != str(self._uprn):
                    continue

            # Extract bin type from Subject field (e.g., "GREY BIN 240L" -> "Grey Bin")
            subject = event.get("Subject", "")
            bin_type_match = re.search(REGEX_BIN_TYPE, subject)
            if not bin_type_match:
                # Skip entries without a recognised bin type
                continue

            bin_type = bin_type_match.group("bin_type").strip().title()

            # Parse the start time (ISO format: "2025-10-10T00:00:00")
            start_time = event.get("StartTime", "")
            try:
                collection_date = datetime.fromisoformat(start_time).date()
            except (ValueError, AttributeError):
                # Skip events with invalid dates
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        if not entries:
            if self._uprn is not None:
                raise Exception(
                    f"No collection events found for UPRN {self._uprn}. "
                    "Please check that this property is registered on your waste portal account."
                )
            else:
                raise Exception(
                    "No collection events found. Please ensure your property is registered on the waste portal."
                )

        return entries
