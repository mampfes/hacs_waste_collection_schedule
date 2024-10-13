import datetime
import xml.etree.ElementTree as ET

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Cannock Chase Council"
DESCRIPTION = "Source for cannockchasedc.gov.uk services for Cannock Chase Council, UK."
URL = "https://www.cannockchasedc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100031640287", "postcode": "WS15 1DN"},
    "Test_002": {"uprn": "100031640289", "postcode": "WS15 1DN"},
    "Test_003": {"uprn": "100031624295", "postcode": "WS11 6DY"},
    "Test_004": {"uprn": "10008163213", "postcode": "WS11 7UD"},
}

API_URL = "https://ccdc.opendata.onl/DynamicCall.dll"
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
        "postcode": "Postcode of the property",
    },
}

SERVICE_NAME_MAP = {
    "Refuse Collection Service": "Refuse",
    "Recycle Collection Service": "Recycling",
    "Garden Collection Service": "Garden waste",
}


class Source:
    def __init__(self, uprn: str | int, postcode: str):
        self._uprn: str = str(uprn).zfill(12)
        self._postcode: str = postcode

    def fetch(self) -> list[Collection]:
        args = {
            "Method": "CollectionDates",
            "UPRN": self._uprn,
            "Postcode": self._postcode,
        }

        r = requests.post(API_URL, data=args)
        r.raise_for_status()

        ns = {"ws": "http://webservices.whitespacews.com/"}
        tree = ET.fromstring(r.text)

        success_flag = tree.find(".//ws:SuccessFlag", ns).text
        if success_flag != "true":
            error_code = tree.find(".//ws:ErrorCode", ns).text
            error_description = tree.find(".//ws:ErrorDescription", ns).text

            # API response for invalid UPRN includes:
            #   <ErrorCode>6</ErrorCode>
            #   <ErrorDescription>No results returned</ErrorDescription>
            if error_code == "6":
                raise SourceArgumentException(
                    "uprn", "UPRN is invalid or outside the Cannock Chase Council area"
                )

            raise Exception(f"API returned error: {error_description}")

        entries = []

        for collection in tree.findall(".//ws:Collection", ns):
            date = collection.find("ws:Date", ns).text
            service = collection.find("ws:Service", ns).text
            service_name = SERVICE_NAME_MAP.get(service)
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(date, "%d/%m/%Y %H:%M:%S").date(),
                    t=service_name,
                    icon=ICON_MAP.get(service_name.upper()),
                )
            )

        return entries
