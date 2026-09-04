import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Invercargill City Council"
DESCRIPTION = "Source for Invercargill City Council rubbish collection."
URL = "https://www.icc.govt.nz"
API_URL = "https://www.icc.govt.nz/client-api/icc/rubbish/search"

# Full test cases included for GitHub validation
TEST_CASES = {
    "Monday - Gladstone Terrace": {"address": "32 Gladstone Terrace, Invercargill"},
    "Tuesday - King Street": {"address": "15 King Street, Invercargill"},
    "Wednesday - Leet Street": {"address": "132 Leet Street, Invercargill"},
    "Thursday - Rodney Street": {"address": "20 Rodney Street, Invercargill"},
    "Friday - Lothian Crescent": {"address": "34 Lothian Crescent, Invercargill"},
    "Friday - Chesney Street": {"address": "69 Chesney Street, Invercargill"},
}

ICON_MAP = {
    "Red Week": "mdi:trash-can",
    "Yellow Week": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the Invercargill City Council rubbish and recycling page and search for your property address.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address, e.g. '69 Chesney Street, Invercargill'",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        # Disguise the script and use the correct Referer URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Referer": "https://www.icc.govt.nz/services/rubbish-recycling/bin-collections"
        }
        
        # Use a GET request with 'params' instead of a POST request with 'data'
        response = requests.get(
            API_URL, params={"address": self._address}, headers=headers, timeout=30
        )
        response.raise_for_status()

        if not response.text.strip():
            return []

        data = response.json()
        entries = []

        # Safely loop through the dates and handle any potential blank entries
        for item in data.get("NextDates", []):
            date_str = item.get("Date")
            week_type = item.get("Week")

            if not date_str or not week_type:
                continue

            try:
                collection_date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=week_type,
                    icon=ICON_MAP.get(week_type),
                )
            )

        # ---------------------------------------------------------------------
        # Fix for Home Assistant restart on collection day:
        # The ICC API server drops today's collection from 'NextDates' after 07:00 AM.
        # If today is the property's scheduled collection day (7 days prior to the first
        # future date), reconstruct today's collection using the alternating week cycle.
        # To revert, simply remove this block down to 'return entries'.
        # ---------------------------------------------------------------------
        if entries:
            today = datetime.date.today()
            first_entry = entries[0]
            prev_date = first_entry.date - datetime.timedelta(days=7)
            if prev_date == today and today not in [e.date for e in entries]:
                prev_week_type = (
                    "Yellow Week" if first_entry.type == "Red Week" else "Red Week"
                )
                entries.insert(
                    0,
                    Collection(
                        date=today,
                        t=prev_week_type,
                        icon=ICON_MAP.get(prev_week_type),
                    ),
                )

        return entries
