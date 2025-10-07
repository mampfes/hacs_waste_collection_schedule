from datetime import datetime, timedelta
from time import time_ns
import logging

import requests
from waste_collection_schedule import Collection

LOGGER = logging.getLogger(__name__)
TITLE = "Waltham Forest"
DESCRIPTION = "Source for Waltham Forest."
URL = "https://walthamforest.gov.uk/"
TEST_CASES = {
    "200001421821": {"uprn": "200001421821"},
    "100023583909": {"uprn": 100022551607},
}


ICON_MAP = {
    "DOMESTIC WASTE COLLECTION SERVICE": "mdi:trash-can",
    "FOOD WASTE COLLECTION SERVICE": "mdi:food",
    "ORGANIC COLLECTION SERVICE": "mdi:leaf",
    "RECYCLING COLLECTION SERVICE": "mdi:recycle",
}


HEADERS = {
    "user-agent": "Mozilla/5.0",
}

class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        # This request gets the session ID
        sid_request = s.get(
            "https://portal.walthamforest.gov.uk/authapi/isauthenticated?uri=https%253A%252F%252Fportal.walthamforest.gov.uk%252FAchieveForms%252F%253Fmode%253Dfill%2526consentMessage%253Dyes%2526form_uri%253Dsandbox-publish%253A%252F%252FAF-Process-d62ccdd2-3de9-48eb-a229-8e20cbdd6393%252FAF-Stage-8bf39bf9-5391-4c24-857f-0dc2025c67f4%252Fdefinition.json%2526process%253D1%2526process_uri%253Dsandbox-processes%253A%252F%252FAF-Process-d62ccdd2-3de9-48eb-a229-8e20cbdd6393%2526process_id%253DAF-Process-d62ccdd2-3de9-48eb-a229-8e20cbdd6393&hostname=portal.walthamforest.gov.uk&withCredentials=true",
            headers=HEADERS,
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Property": {
                    key: {"value": self._uprn}
                    for key in ["AccountSiteUprn", "UPRNSearch", "calcUPRN", "customerUPRN", "inputUPRN"]
                }
            }
        }

        schedule_request = s.post(
            f"https://portal.walthamforest.gov.uk/apibroker/runLookup?id=5e208cda0d0a0&repeat_against=&noRetry=False&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}sid={sid}",
            headers=HEADERS,
            json=payload,
        )
        rowdata = schedule_request.json()["integration"]["transformed"]["rows_data"]

        # Extract bin types and next collection dates
        entries = []
        today = datetime.today()
        for item in rowdata.values():
            bin_type = item["ServiceName"]
            next_date = item["NextCollectionDate"]
            if next_date == " NaN ":
                continue
            # Schedule reported in %A %d %B format, e.g. Thursday 20 February
            # This is an awful format at a year boundary and requires iteration to pull out a real date object.
            # Would use %-d for day of month with no leading 0, but that is not OS independent, hence horrible strip
            attempts = 40
            attempt_date = today
            attempt_formatted_for_comparison = f"{attempt_date.strftime('%A')} {attempt_date.strftime('%d').lstrip('0')} {attempt_date.strftime('%B')}"
            found = attempt_formatted_for_comparison == next_date
            while not found and attempts > 0:
                attempt_date += timedelta(days=1)
                attempt_formatted_for_comparison = f"{attempt_date.strftime('%A')} {attempt_date.strftime('%d').lstrip('0')} {attempt_date.strftime('%B')}"
                found = attempt_formatted_for_comparison == next_date
                attempts -= 1

            if not found:
                LOGGER.error(f'Failing to find the date - API returned {next_date}, last date attempted was {attempt_date}')
                continue

            entries.append(
                Collection(
                    t=bin_type,
                    date=attempt_date.date(),
                    icon=ICON_MAP.get(bin_type.upper()),
                )
            )

        return entries
