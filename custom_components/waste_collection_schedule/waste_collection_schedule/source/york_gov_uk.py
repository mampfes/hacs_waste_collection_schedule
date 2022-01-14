from datetime import datetime, timedelta
import json
from urllib.parse import quote

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "York.gov.uk"
DESCRIPTION = "Source for York.gov.uk services for the city of York, UK."
URL = "https://york.gov.uk"
TEST_CASES = {}
TEST_CASES = {
    "Reighton Avenue, York": {
        "uprn": "100050580641",
    },
    "Granary Walk, York": {
        "uprn": "010093236548",
    },
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://waste-api.york.gov.uk/api/GetBinCollectionDataForUprn/{self._uprn}"
        )

        # extract data from json
        data = json.loads(r.text)

        # Map to better format to work with
        serviceData = {}

        for service in data["services"]:
            serviceData[service["service"]] = service["nextCollection"]

            lastCollected = datetime.fromisoformat(service["lastCollected"])

            # York data will never show "today" unless we check for last collected
            if lastCollected.date() == datetime.today().date():
                serviceData[service["service"]] = service["lastCollected"]

        # create entries for trash, recycling, and yard waste
        entries = []

        try:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        serviceData["REFUSE"], "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    t="Trash",
                    icon="mdi:trash-can",
                )
            )
        except ValueError:
            pass  # ignore date conversion failure for not scheduled collections

        try:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        serviceData["RECYCLING"], "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    t="Recycling",
                    icon="mdi:recycle",
                )
            )
        except ValueError:
            pass  # ignore date conversion failure for not scheduled collections

        try:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        serviceData["GARDEN"], "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    t="Yard Waste",
                    icon="mdi:leaf",
                )
            )
        except ValueError:
            pass  # ignore date conversion failure for not scheduled collections

        return entries

