from datetime import datetime

import requests
import urllib3
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


TITLE = "Hastings Borough Council"
DESCRIPTION = "Source for hastings.gov.uk services for Hastings Borough Council, UK."
URL = "https://www.hastings.gov.uk/"
API_URL = "https://el.hastings.gov.uk/MyArea/CollectionDays.asmx/LookupCollectionDaysByService"
TEST_CASES = {
    "Test_001": {"postcode": "TN34 1QF", "house_number": 36, "uprn": 100060038877},
    "Test_002": {"postcode": "TN34 2DL", "house_number": "28A", "uprn": "10070609836"},
    "Test_003": {"postcode": "TN37 7QH", "house_number": 5, "uprn": "100060041770"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode (Deprecated, leave empty)",
        "house_number": "House Number (Deprecated, leave empty)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
        "postcode": "Deprecated, leave mpty, will be ignored",
        "house_number": "Deprecated, leave mpty, will be ignored",
    }
}


class Source:
    def __init__(
        self,
        uprn: str | int,
        postcode: (
            str | None
        ) = None,  # Not used but kept for compatibility with old version
        house_number: (
            str | int | None
        ) = None,  # Not used but kept for compatibility with old version
    ):
        self._uprn = str(uprn)

    def fetch(self):
        payload = {"Uprn": self._uprn}

        r = requests.post(API_URL, json=payload, verify=False)
        r.raise_for_status()

        data = r.json()["d"]

        entries = []
        for service in data:
            waste_type: str = (
                service["Service"].removesuffix("collection service").strip()
            )
            icon = ICON_MAP.get(waste_type)
            date_str: str

            for date_str in service["Dates"]:
                entries.append(
                    Collection(
                        date=datetime.fromtimestamp(
                            int(date_str.strip("/").removeprefix("Date").strip("()"))
                            / 1000
                        ).date(),
                        t=waste_type,
                        icon=icon,
                    )
                )

        return entries
