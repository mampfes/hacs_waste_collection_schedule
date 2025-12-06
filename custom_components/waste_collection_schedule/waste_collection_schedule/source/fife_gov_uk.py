import requests
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Fife Council"
DESCRIPTION = "Source for Fife Council."
URL = "https://www.fife.gov.uk"
TEST_CASES = {
    "SANDYHILL ROAD, ST ANDREWS": {"uprn": 320069186},
    "CERES ROAD, PITSCOTTIE": {"uprn": 320063641},
    "SHORE ROAD, BALMALCOLM": {"uprn": "320083539"},
    "CANMORE STREET, DUNFERMLINE": {"uprn": "320101510"},
}
ICON_MAP = {
    "Blue": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Brown": "mdi:leaf",
    "Grey": "mdi:package-variant",
    "Green": "mdi:recycle",
}

API_BASE_URL = "https://fife.form.uk.empro.verintcloudservices.com/api"
API_URL = f"{API_BASE_URL}/custom"
AUTH_URL = f"{API_BASE_URL}/citizen"

DATE_FORMAT = "%A, %B %d, %Y"
REQUEST_TIMEOUT = 10  # seconds


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = str(uprn)

    def fetch(self):
        """Fetch bin calendar collections for the given UPRN from Fife Council."""
        session = requests.Session()

        # Get authentication token
        auth_response = session.get(
            AUTH_URL,
            params={"preview": "false", "locale": "en"},
            timeout=REQUEST_TIMEOUT,
        )
        auth_response.raise_for_status()

        auth_token = auth_response.headers.get("Authorization")
        if not auth_token:
            raise ValueError("No authorization token received from API")

        session.headers.update({"Authorization": auth_token})

        # Get collection data
        api_response = session.post(
            API_URL,
            params={
                "action": "powersuite_bin_calendar_collections",
                "actionedby": "bin_calendar",
                "loadform": True,
                "access": "citizen",
                "locale": "en",
            },
            json={"name": "bin_calendar", "data": {"uprn": self._uprn}},
            timeout=REQUEST_TIMEOUT,
        )
        api_response.raise_for_status()

        # Parse response data
        response_data = api_response.json()
        data = response_data.get("data", {})

        if data.get("results_returned") == "false":
            raise ValueError(f"No results returned for UPRN: {self._uprn}")

        collections = data.get("tab_collections", [])
        if not collections:
            raise ValueError(f"No collection data found for UPRN: {self._uprn}")

        entries = []
        for collection in collections:
            try:
                date_str = collection.get("date")
                if not date_str:
                    continue

                date = datetime.strptime(date_str, DATE_FORMAT).date()
                collection_type = collection.get("type", "")
                colour = collection.get("colour", "")
                icon = ICON_MAP.get(colour)

                entries.append(
                    Collection(date=date, t=collection_type, icon=icon)
                )
            except (ValueError, KeyError):
                # Skip invalid date entries but continue processing others
                continue

        return entries
