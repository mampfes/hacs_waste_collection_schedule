import datetime
import json
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, exceptions

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

EVENTS_REGEX = re.compile(
    r"eventSettings.*?dataSource.*?isJson\((\[.*?\])\)", re.DOTALL
)


class Source:
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def fetch(self):
        if not self._username:
            raise exceptions.SourceArgumentRequired("username")
        if not self._password:
            raise exceptions.SourceArgumentRequired("password")

        session = requests.Session()
        login_url = f"{URL}/Identity/Account/Login"
        data_url = URL

        response = session.get(login_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        token_element = soup.find("input", attrs={"name": "__RequestVerificationToken"})
        if token_element is None:
            raise ValueError("Unable to find anti-forgery token")
        token = token_element.get("value")
        if not token:
            raise ValueError("Unable to find anti-forgery token")

        # Log in to the website
        login_payload = {
            "Input.Email": self._username,
            "Input.Password": self._password,
            "__RequestVerificationToken": token,
            "Input.RememberMe": "false",
        }
        response = session.post(login_url, data=login_payload)
        response.raise_for_status()
        if "/Identity/Account/Login" in response.url:
            raise exceptions.SourceArgumentException(
                argument="username",
                message="Login failed. Please check your username and password.",
            )

        # Fetch the collection data
        response = session.get(data_url)
        response.raise_for_status()

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
