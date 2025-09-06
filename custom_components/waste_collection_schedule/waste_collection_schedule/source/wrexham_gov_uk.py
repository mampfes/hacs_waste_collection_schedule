import json
from datetime import datetime
from time import time_ns
from bs4 import BeautifulSoup, NavigableString

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wrexham County Borough Council"
DESCRIPTION = "Source for Wrexham County Borough Council."
URL = "https://www.wrexham.gov.uk/"
TEST_CASES = {
    "Duck Farm, Gresford, LL12 8YT": { "uprn": "100100940408"},
    "Regent St, Wrexham, LL11 1SA": { "uprn": "100100938112"},
    "Hill Crest, Wrexham, LL13 8RN": { "uprn": "100100860092"}
}

API_URL = "https://www.wrexham.gov.uk/service/when-are-my-bins-collected"

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

ICON_MAP = {
    "recycling": "mdi:recycle",
    "food": "mdi:food-apple",
    "general": "mdi:trash-can",
    "garden": "mdi:leaf",
}

TYPE_MAP = {
    "recycling": "Recycling",
    "food": "Food Waste",
    "general": "General Waste",
    "garden": "Garden Waste",
}

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()
        s.headers.update(HEADERS)

        # This request gets the session ID
        sid_request = s.get(
            "https://myaccount.wrexham.gov.uk/authapi/isauthenticated",
            params={
                "uri": "https://myaccount.wrexham.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-ceb55423-9f5d-4124-b713-805ac7a73e3e/AF-Stage-854336b9-1221-4e6a-88d7-785fb2f8e340/definition.json&redirectlink=/en&cancelRedirectLink=/en&consentMessage=yes&noLoginPrompt=1",
                "hostname": "myaccount.wrexham.gov.uk",
                "withCredentials": True,
            },
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        s.get(
            "https://myaccount.wrexham.gov.uk/apibroker/domain/myaccount.wrexham.gov.uk",
            params={"_": timestamp, "sid": sid},
        )

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Section 1": {
                    "UPRN": {
                        "value": self._uprn
                    },
                    "NoWeeks":  {
                        "name": "NoWeeks",
                        "value": "2",
                    },
                }
            }
        }
        params = {
            "id": "5beab9a792bb5",
            "repeat_against": "",
            "noRetry": False,
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": timestamp,
            "sid": sid,
        }

        schedule_request = s.post(
            "https://myaccount.wrexham.gov.uk/apibroker/runLookup",
            params=params,
            json=payload,
        )

        rowdata = json.loads(schedule_request.content)["integration"]["transformed"][
            "rows_data"
        ]

        html_content = rowdata['0']['UpcomingCollections']

        soup = BeautifulSoup(html_content, 'html.parser')

        entries = []

        #Loop through the whole table and convert to bin days
        for row in soup.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) >= 2:
                date_str = cells[0].text.strip()
                bins = cells[1].find_all("li")

                for bin_item in bins:
                    text = bin_item.get_text(strip=True).lower()

                    date = datetime.strptime(date_str, "%d/%m/%Y").date()

                    if "recycling" in text:
                        entries.append(
                          Collection(
                              t = TYPE_MAP["recycling"],
                              date = date,
                              icon = ICON_MAP["recycling"],
                          )
                        )
                    if "food" in text:
                        entries.append(
                          Collection(
                              t = TYPE_MAP["food"],
                              date = date,
                              icon = ICON_MAP["food"],
                          )
                        )
                    if "garden" in text:
                        entries.append(
                          Collection(
                              t = TYPE_MAP["garden"],
                              date = date,
                              icon = ICON_MAP["garden"],
                          )
                        )
                    if "general" in text:
                        entries.append(
                          Collection(
                              t = TYPE_MAP["general"],
                              date = date,
                              icon = ICON_MAP["general"],
                          )
                        )

        return entries