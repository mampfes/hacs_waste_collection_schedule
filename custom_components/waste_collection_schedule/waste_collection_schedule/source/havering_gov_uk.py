import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Havering"
DESCRIPTION = "Source for London Borough of Havering."
URL = "https://www.havering.gov.uk/"
TEST_CASES = {
    "53 Argyle Gardens": {"uprn": "100021403735"}
}

COLLECTION_MAP = {
    "Service - Domestic Waste": {
        "waste_type": "Domestic Waste",
        "icon": "mdi:trash-can",
    },
    "Service - Garden Waste": {
        "waste_type": "Garden Waste",
        "icon": "mdi:leaf",
    },
    "Service - Recycling": {
        "waste_type": "Recycling",
        "icon": "mdi:recycle",
    },
        "Service - Garden Waste Winter": {
        "waste_type": "Garden Waste Winter",
        "icon": "mdi:leaf",
    },
}

API_URL = "https://api-prd.havering.gov.uk/whitespace/GetCollectionByUprnAndDate"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self):
        payload = {
            "getCollectionByUprnAndDate": {
                "getCollectionByUprnAndDateInput": {
                    "uprn": self._uprn,
                    "nextCollectionFromDate": datetime.datetime.today().strftime("%Y/%m/%d")
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Trace": "true",
            "Ocp-Apim-Subscription-Key": "545bcf53c9094dfd980dd9da72b0514d"
        }
        r = requests.post(API_URL, json=payload, headers=headers)
        data = r.json()

        entries = []

        for next_collection in data["getCollectionByUprnAndDateResponse"]["getCollectionByUprnAndDateResult"]["Collections"]:
            collection_type = COLLECTION_MAP[next_collection["service"]]
            collection_date = next_collection["date"]
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(collection_date, "%d/%m/%Y %H:%M:%S").date(),
                    t=collection_type["waste_type"],
                    icon=collection_type["icon"],
                )
            )

        return entries
