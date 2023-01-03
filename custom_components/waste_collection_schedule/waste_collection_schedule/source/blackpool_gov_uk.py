import requests

from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Blackpool Council"
DESCRIPTION = "Source for blackpool.gov.uk"
URL = "https://blackpool.gov.uk"

BINDAY_URL_TOKEN = "https://api.blackpool.gov.uk//api/bartec/security/token"
BINDAY_URL_SCHEDULE = "https://api.blackpool.gov.uk//api/bartec/collection/PremiseJobs"
ICON_MAP = {
    "Blue Bin": "mdi:recycle",
    "Grey bin or Red sack": "mdi:trash-can",
    "Green bin or Garden waste": "mdi:leaf",
    "Commercial Refuse": "mdi:trash-can",
}


class Source:
    """Waste collection source for blackpool.gov.uk"""
    def __init__(self, postcode=None, address=None, uprn=None):
        self._postcode = postcode
        self._address = address
        self._uprn = uprn

        if postcode is None and address is None and uprn is None:
            raise Exception("no attributes - specify uprn")

    def fetch(self):
        if self._uprn is None:
            raise Exception("Error querying calendar data, missing UPRN")

        response = requests.get(BINDAY_URL_TOKEN)
        response.raise_for_status()
        token = response.json()
        entries = []

        jsonData = {
            "UPRN": self._uprn,
            "USRN": "",
            "PostCode": self._postcode,
            "StreetNumber": self._address,
            "CurrentUser": {"UserId": "", "Token": token},
        }

        headers = {"Accept": "*/*", "Content-Type": "application/json"}

        response = requests.post(
            BINDAY_URL_SCHEDULE, json=jsonData, headers=headers
        )
        response.raise_for_status()
        waste = response.json()["jobsField"]

        for data in waste:
            collectionDate = datetime.strptime(
                data["jobField"]["scheduledStartField"], "%Y-%m-%dT%H:%M:%S"
            ).date()
            collectionType = self.binType(data["jobField"]["nameField"])
            collectionIcon = ICON_MAP.get(collectionType)
            entries.append(Collection(collectionDate, collectionType, collectionIcon))

        return entries

    def binType(self, collectionType: str) -> str:
        """Convert collection type to bin color/type"""
        if collectionType == "Empty Commercial Refuse":
            return "Commercial Refuse"
        if collectionType == "Empty Dry Recycling 140L":
            return "Blue Bin"
        if collectionType.startswith("Empty Domestic Refuse"):
            return "Grey bin or Red sack"
        if collectionType.startswith("Empty Green Waste"):
            return "Green bin or Garden waste"
        return collectionType
