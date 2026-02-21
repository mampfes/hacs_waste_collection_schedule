import re
from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "Blaby District Council"
DESCRIPTION = "Source for blaby.gov.uk services for Blaby district, UK."
URL = "https://blaby.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 100030407500},
    "Test_002": {"uprn": "100030395499"},
    "Test_003": {"uprn": "010001238216"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Refuse": "mdi:trash-can",
    "Garden": "mdi:leaf",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details",
    }
}
REGEX = r"\d+\/\d+\/\d+"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()
        payload: dict = {"ref": self._uprn, "redirect": "collections"}
        r = s.get(
            "https://my.blaby.gov.uk/set-location.php",
            verify=False,
            params=payload,
            headers=HEADERS,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.content, "html.parser")
        waste_collections = soup.find_all("span", {"class": "box-item"})

        entries = []

        for waste_collection in waste_collections:
            # Garden waste is a subscription service, catch
            # error and skip processing when no dates shown
            try:
                waste_dates = waste_collection.find_all("strong")
                waste_days = re.findall(REGEX, waste_dates[0].text)
            except IndexError:
                break

            waste_type = waste_collection.find_all("h2")
            if waste_days:
                for item in waste_days:
                    entries.append(
                        Collection(
                            t=waste_type[0].text,
                            date=datetime.strptime(item, "%d/%m/%Y").date(),
                            icon=ICON_MAP.get(waste_type[0].text),
                        )
                    )

        return entries
