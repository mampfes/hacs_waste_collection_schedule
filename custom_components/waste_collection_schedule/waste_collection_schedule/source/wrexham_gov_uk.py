import json
from datetime import datetime
from time import time_ns
from bs4 import BeautifulSoup, NavigableString

import requests

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
    "recycling-bin": "mdi:recycle",
    "general-bin": "mdi:trash-can",
    "garden-bin": "mdi:leaf",
}

TYPE_MAP = {
    "recycling-bin": "Recycling / Food",
    "general-bin": "General Waste",
    "garden-bin": "Garden Waste"
}

class Source:
    def __init__(self,  uprn: str | int, postcode=None):
        self._uprn: str = str(uprn).zfill(12)

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

        collection_data = []

        rows = soup.find_all('tr')[1:]  # Skip the first row (table headers)

        #Loop through the whole table and convert to bin days
        for row in soup.find_all('tr'):
            cells = row.find_all('td')

            if len(cells) >= 2:
                date_str = cells[0].text.strip()
                bins = cells[1].find_all('li')

                try:
                    base_date = datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    # Skip this row if the date is invalid
                    continue

                for bin_item in bins:
                    bin_key = bin_item.get('class', [None])[0]

                    bin_type = TYPE_MAP.get(bin_key)
                    bin_icon = ICON_MAP.get(bin_key)

                    collection_data.append({
                        't': bin_type,
                        'icon': bin_icon,
                        'date': base_date.strftime("%d/%m/%Y")
                    })

        return collection_data
