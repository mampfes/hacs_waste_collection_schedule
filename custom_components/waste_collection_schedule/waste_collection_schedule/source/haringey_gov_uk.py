from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Haringey Council"
DESCRIPTION = "Source for haringey.gov.uk services for Haringey Council, UK."
URL = "https://www.haringey.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "100021209182"},
    "Test_002": {"uprn": "100021207181"},
    "Test_003": {"uprn": "100021202738"},
    "Test_004": {"uprn": 100021202131},
}
ICON_MAP = {
    "Non-Recyclable Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food Waste": Icons.BIO_KITCHEN,
    "Garden Waste": Icons.GARDEN,
}

SOURCE_CODEOWNERS = ["@marcjay"]

API = "https://wastecollections.haringey.gov.uk/api"
COUNCIL_ID = "45"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        session = requests.Session()

        # Step 1: resolve the UPRN to the internal point id.
        address_response = session.post(
            f"{API}/getAddressByPointId",
            json={
                "pointId": self._uprn,
                "councilId": COUNCIL_ID,
                "pointType": "PointAddress",
            },
            timeout=30,
        )
        address_response.raise_for_status()
        addresses = address_response.json().get("data", [])
        if not addresses:
            raise SourceArgumentNotFound("uprn", self._uprn)
        point_id = addresses[0]["id"]

        # Step 2: fetch the collection schedule for that point id.
        collection_response = session.post(
            f"{API}/getCollectionDays",
            json={
                "pointId": point_id,
                "pointType": "PointAddress",
                "councilId": COUNCIL_ID,
            },
            timeout=30,
        )
        collection_response.raise_for_status()
        services = collection_response.json().get("activeServices", [])

        entries = []
        for service in services:
            waste_type = service.get("taskTypeName") or service.get("serviceName")
            for schedule in service.get("serviceSchedules", []):
                date_str = schedule.get("currentScheduledDate")
                if not date_str:
                    continue
                entries.append(
                    Collection(
                        date=datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        ).date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
