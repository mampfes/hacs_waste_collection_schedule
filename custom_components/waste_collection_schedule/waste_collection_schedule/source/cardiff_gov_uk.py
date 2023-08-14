import datetime
import json
import xml.etree.ElementTree as ET

import requests
from waste_collection_schedule import Collection

TITLE = "Cardiff Council"
DESCRIPTION = "Source script for cardiff.gov.uk"
URL = "https://cardiff.gov.uk"
TEST_CASES = {
    "Glass": {"uprn": "100100124569"},
    "NoGlass": {"uprn": "100100127440"},
}

ICON_MAP = {
    "General": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Food": "mdi:food",
    "Glass": "mdi:glass-fragile",
}

PAYLOAD_GET_JWT = (
    "<?xml version='1.0' encoding='utf-8'?>"
    "<soap:Envelope xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'"
    " xmlns:xsd='http://www.w3.org/2001/XMLSchema'"
    " xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'>"
    "<soap:Body>"
    "<GetJWT xmlns='http://tempuri.org/' />"
    "</soap:Body>"
    "</soap:Envelope>"
)

URL_COLLECTIONS = "https://api.cardiff.gov.uk/WasteManagement/api/WasteCollection"
URL_GET_JWT = (
    "https://authwebservice.cardiff.gov.uk/AuthenticationWebService.asmx?op=GetJWT"
)


def get_headers() -> dict[str, str]:
    """Return common headers that every request to the Cardiff API requires."""
    return {
        "Origin": "https://www.cardiff.gov.uk",
        "Referer": "https://www.cardiff.gov.uk/",
        "User-Agent": "Mozilla/5.0",
    }


def get_token() -> str:
    """Get an access token."""
    headers = get_headers()
    headers.update(
        {
            "Content-Type": 'text/xml; charset="UTF-8"',
        }
    )
    r = requests.post(URL_GET_JWT, headers=headers, data=PAYLOAD_GET_JWT)
    r.raise_for_status()

    tree = ET.fromstring(r.text)

    jwt_result_element = tree.find(
        ".//GetJWTResult", namespaces={"": "http://tempuri.org/"}
    )

    if jwt_result_element is None or jwt_result_element.text is None:
        raise Exception("could not find Token")
    jwt_result = jwt_result_element.text

    token = json.loads(jwt_result)["access_token"]
    return token


class Source:
    def __init__(self, uprn=None):
        self._uprn = uprn

    def fetch(self):
        payload_waste_collections = {
            "systemReference": "web",
            "language": "eng",
            "uprn": self._uprn,
        }

        entries = []

        jwt = get_token()
        client = requests.Session()
        headers = get_headers()
        headers.update({"Authorization": f"Bearer {jwt}"})

        r = client.post(
            URL_COLLECTIONS, headers=headers, json=payload_waste_collections
        )
        r.raise_for_status()
        collections = r.json()

        for week in collections["collectionWeeks"]:
            for bin in week["bins"]:
                entries.append(
                    Collection(
                        date=datetime.datetime.fromisoformat(week["date"]).date(),
                        t=bin["type"],
                        icon=ICON_MAP.get(bin["type"]),
                    )
                )
        return entries
