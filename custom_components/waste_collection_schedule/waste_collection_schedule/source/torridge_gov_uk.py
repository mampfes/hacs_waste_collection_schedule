import json
from datetime import datetime, timedelta
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Torridge Council"
DESCRIPTION = "Source for torridge.gov.uk services for Torridge, UK."
URL = "https://torridge.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10093911050"},
    "Test_002": {"uprn": 10002296087},
    "Test_003": {"uprn": "200001644184"},
    "Test_004": {"uprn": 100040385608},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
BIN_NAME = {
    "Refuse": "Refuse",
    "Recycling": "Recycling",
    "GardenBin": "Garden",
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}
MONTHS = {
    "January": 1, "Jan": 1,
    "February": 2, "Feb": 2,
    "March": 3, "Mar": 3,
    "April": 4, "Apr": 4,
    "May": 5,
    "June": 6, "Jun": 6,
    "July": 7, "Jul": 7,
    "August": 8, "Aug": 8,
    "September": 9, "Sep": 9,
    "October": 10, "Oct": 10,
    "November": 11, "Nov": 11,
    "December": 12, "Dec": 12,
}
RELATIVE_DATES = {"Today": 0, "Tomorrow": 1}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        s.get(
            f"https://torridgedc-self.achieveservice.com/apibroker/domain/torridgedc-self.achieveservice.com?_={timestamp}",
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://torridgedc-self.achieveservice.com/authapi/isauthenticated?uri=https%3A%2F%2Ftorridgedc-self.achieveservice.com%2Fservice%2FMy_property_information&hostname=torridgedc-self.achieveservice.com&withCredentials=true",
            headers=HEADERS,
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {"formValues": {"Search": {"uprn": {"value": self._uprn}}}}
        schedule_request = s.post(
            f"https://torridgedc-self.achieveservice.com/apibroker/runLookup?id=6583107397653&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload,
        )
        rowdata = json.loads(schedule_request.content)["integration"]["transformed"][
            "rows_data"
        ]

        # Extract bin types and next collection dates
        entries: list[Collection] = []
        current_month = datetime.strftime(datetime.now(), "%b")  # Short month names
        current_year = int(datetime.strftime(datetime.now(), "%Y"))
        today = datetime.today().date()

        for item in rowdata.values():
            for _, value in item.items():
                # Example: "GardenBin: Wed 26 Feb then every alternate  Wed"
                parts = value.split(": ")
                if len(parts) < 2:
                    raise ValueError("Unexpected data format")

                waste_type = parts[0].strip()  # e.g., "GardenBin"
                if waste_type in BIN_NAME:
                    waste_type = BIN_NAME[waste_type]
                else:
                    raise ValueError(f"Unknown waste type: {waste_type}")

                date_part = parts[1].split(" then ")[0].strip()  # e.g., "Wed 26 Feb"

                # Handle "No collection" messages
                if date_part.split()[0].lower() == "no":
                    continue  # Skip entries where collection isn't available

                # Handle "Today" or "Tomorrow"
                if date_part in RELATIVE_DATES:
                    collection_date = today + timedelta(days=RELATIVE_DATES[date_part])
                else:
                    # Extract the date
                    date_parts = date_part.split(" ")
                    if len(date_parts) < 3:
                        raise ValueError("Unexpected date format")

                    bin_day_num, bin_month = date_parts
                    if bin_month not in MONTHS:
                        raise ValueError(f"Unknown month: {bin_month}")

                    # Handle year rollover
                    bin_year = (
                        current_year
                        if MONTHS[bin_month] >= MONTHS[current_month]
                        else current_year + 1
                    )

                    # Convert to date object
                    dt = f"{bin_day_num} {bin_month} {bin_year}"
                    collection_date = datetime.strptime(dt, "%d %b %Y").date()

                # Append valid collections
                entries.append(
                    Collection(
                        t=waste_type,
                        date=collection_date,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
