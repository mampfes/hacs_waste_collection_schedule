from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hart District Council"
DESCRIPTION = "Source for hart.gov.uk services for Hart District Council, UK."
URL = "https://www.hart.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "100060420702"},
    "Test_002": {"uprn": "100061994826"},
    "Test_003": {"uprn": "200003085501"},
    "Test_004": {"uprn": "100062464806"},
}
ICON_MAP = {
    "recycling-collection-service": "mdi:recycle",
    "garden-waste-collection-service": "mdi:leaf",
    "refuse-collection-service": "mdi:trash-can",
    "christmas-collection-dates": "mdi:string-lights",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        r = requests.get(
            URL + "/bbd-whitespace/one-year-collection-dates",
            params={"uprn": self._uprn, "_wrapper_format": "drupal_ajax"},
            timeout=30,
        )
        r.raise_for_status()

        entries = []

        for _, data in r.json()[0]["settings"]["collection_dates"].items():
            for collection in data:
                entries.append(
                    Collection(
                        date=datetime.fromtimestamp(
                            int(collection["timestamp"])
                        ).date(),
                        t=collection["service"],
                        icon=ICON_MAP.get(collection["service-identifier"]),
                    )
                )

        return entries
