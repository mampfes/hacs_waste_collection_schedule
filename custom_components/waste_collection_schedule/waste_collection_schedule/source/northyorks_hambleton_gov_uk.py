# Highly based on milton_keynes_gov_uk.py

import re
from datetime import datetime, timedelta
from time import time_ns

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Yorkshire Council - Hambleton"
DESCRIPTION = "Source for North Yorkshire Council - Hambleton."
URL = "https://northyorks.gov.uk"
TEST_CASES = {
    "010070735142": {"uprn": "010070735142"},
    "100050360667": {"uprn": "100050360667"},
    "010070732324, leading 0 missing": {"uprn": 10070732324},
}


ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "GARDEN": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

DATE_REGEX = r"\d{1,2}\s\w{3,4}\s\d{4}"

API_URL = "https://hambletondc-self.achieveservice.com/service/Bin_collection_finder"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        r = s.get(
            "https://hambletondc-self.achieveservice.com/apibroker/domain/hambletondc-self.achieveservice.com",
            params={
                "_": timestamp,
            },
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://hambletondc-self.achieveservice.com/authapi/isauthenticated",
            params={
                "uri": "https://hambletondc-self.achieveservice.com/service/Bin_collection_finder",
                "hostname": "hambletondc-self.achieveservice.com",
                "withCredentials": "true",
            },
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Address search": {
                    "pccUPRN": {
                        "value": self._uprn
                    },  # Probably not needed but does not hurt
                    "selectedUPRN": {"value": self._uprn},
                    "GWStatusNumLicences_PurchasePeriod": {"value": "1"},
                    "pccNumWeeks": {"value": "23"},
                }
            }
        }
        schedule_request = s.post(
            "https://hambletondc-self.achieveservice.com/apibroker/runLookup",
            headers=HEADERS,
            params={
                # "id": "62b1d2c960a47",
                "id": "5b3254c44316c",
                "repeat_against": "",
                "noRetry": "true",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AF-Renderer::Self",
                "_": str(timestamp),
                "sid": str(sid),
            },
            json=payload,
        )
        rowdata = schedule_request.json()["integration"]["transformed"]["rows_data"]

        # Extract bin types and next collection dates
        entries = []
        for index, item in rowdata.items():
            bin_types = []
            soup = BeautifulSoup(item["pccTableHTML"], "html.parser")
            headline_table, collection_table = soup.find_all("table")[:2]
            for bin_type in headline_table.find_all("td")[1:]:
                if not bin_type.text.strip():
                    continue
                bin_types.append(bin_type.text.strip())

            for collection_table_row in collection_table.find_all("tr"):
                tds = collection_table_row.find_all("td")
                date_str = re.search(DATE_REGEX, tds[0].text.strip()).group()

                date = datetime.strptime(date_str, "%d %b %Y").date()
                for index, td in enumerate(tds[1:]):
                    if td.find("img"):
                        if r := re.search(
                            r"\d+ days? later than usual", td.text.strip()
                        ):
                            delta = int(re.search(r"\d", r.group()).group())
                            date = date + timedelta(days=delta)
                        icon = ICON_MAP.get(bin_types[index].upper())
                        entries.append(
                            Collection(t=bin_types[index], date=date, icon=icon),
                        )
        return entries
