from datetime import date, datetime

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "London Borough of Camden"
DESCRIPTION = "Source for London Borough of Camden."
URL = "https://www.camden.gov.uk/"
COUNTRY = "uk"
TEST_CASES = {
    "Red Lion Street": {"uprn": 5121151},
}


ICON_MAP = {
    "rubbish collection": Icons.GENERAL_WASTE,
    "domestic refuse collection": Icons.GENERAL_WASTE,
    "garden waste collection": Icons.GARDEN,
    "domestic garden collection": Icons.GARDEN,
    "food collection": Icons.BIO_KITCHEN,
    "domestic food collection": Icons.BIO_KITCHEN,
    "recycling collection": Icons.RECYCLING,
    "domestic dmr collection": Icons.RECYCLING,
}


BASE_URL = "https://recyclingandrubbishcollections.camden.gov.uk"
API_CALENDAR_DATA = f"{BASE_URL}/api/getCalendarData"
COUNCIL_ID = "27"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)
        self._session = requests.Session(impersonate="chrome")

    def fetch(self) -> list[Collection]:
        response = self._session.post(
            API_CALENDAR_DATA,
            json={"councilId": COUNCIL_ID, "uprn": self._uprn},
            headers={"content-type": "application/json", "x-recaptcha-token": ""},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        if data.get("message") != "OK":
            raise ValueError(
                f"API advised error (HTTP {response.status_code}, UPRN {self._uprn}): {data.get('message')}"
            )

        entries = []
        today = date.today()

        for data_item in data.get("data", []):
            for record in data_item.get("records", []):
                scheduled_date = record.get("actual_scheduled_date")
                service = record.get("service", "").strip()
                if not scheduled_date or not service:
                    continue

                collection_date = datetime.fromisoformat(
                    scheduled_date.replace("Z", "+00:00")
                ).date()
                if collection_date < today:
                    continue

                icon = ICON_MAP.get(service.lower())
                entries.append(Collection(date=collection_date, t=service, icon=icon))

        return entries
