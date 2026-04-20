import datetime
import json
import re
from waste_collection_schedule import Collection, exceptions
import requests
from bs4 import BeautifulSoup

TITLE = "Havant Borough Council"
DESCRIPTION = "Source for Havant Borough Council waste collection."
URL = "https://waste.havant.gov.uk"
TEST_CASES = {
    "Test Case 1": {
        "username": "!secret waste_havant_gov_uk_username",
        "password": "!secret waste_havant_gov_uk_password",
    },
}

ICON_MAP = {
    "Residual 240L": "mdi:trash-can",
    "Recycling 240L": "mdi:recycle",
}

EVENTS_REGEX = re.compile(r"eventSettings.*dataSource.*isJson\((\[.*\])\)", re.DOTALL)


class Source:
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def fetch(self):
        if not self._username or not self._password:
            raise exceptions.SourceArgumentException(
                argument="username and password",
                message="Both username and password must be provided.",
            )
        session = requests.Session()
        login_url = f"{URL}/Identity/Account/Login"
        data_url = URL

        response = session.get(login_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        token_element = soup.find("input", attrs={"name": "__RequestVerificationToken"})
        token = token_element["value"]

        # Log in to the website
        login_payload = {
            "Input.Email": self._username,
            "Input.Password": self._password,
            "__RequestVerificationToken": token,
            "Input.RememberMe": "false",
        }
        response = session.post(login_url, data=login_payload)
        if response.status_code < 200 or response.status_code >= 400:
            raise exceptions.SourceArgumentException(
                argument="username and password",
                message="Login failed. Please check your username and password.",
            )

        # Fetch the collection data
        response = session.get(data_url)

        matches = EVENTS_REGEX.search(response.text)
        if not matches:
            raise ValueError("Could not find collection data in the page")
        events_json = json.loads(matches.group(1))

        entries = []
        for event in events_json:
            date = datetime.datetime.strptime(
                event["StartTime"], "%Y-%m-%dT%H:%M:%S"
            ).date()
            waste_type = event["Subject"].strip()
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                )
            )

        return entries
