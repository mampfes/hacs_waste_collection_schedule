import json
from datetime import date, datetime, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Norfolk District Council"
DESCRIPTION = "Source for waste collection services for North Norfolk District Council"
URL = "https://www.north-norfolk.gov.uk/"

HEADERS = {"user-agent": "Mozilla/5.0"}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

# Note: running test cases in quick succession can cause website to refuse connection.
# Test_003 may return an error. A workaround is to add sleep(5) to the fetch.
# Shouldn't be an issue with normal HA use for single addresses.
TEST_CASES = {
    "Test_001": {
        "uprn": "100090878875",
    },
    "Test_002": {
        "uprn": 100090883974,
    },
    "Test_003": {
        "uprn": "100090880632",
    },
}

ICON_MAP = {
    "Grey bin": "mdi:trash-can",
    "Green bin": "mdi:recycle",
    "Brown bin": "mdi:leaf",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def append_year(self, d: str) -> date:
        # Website doesn't return the year.
        # Append the current year, and then check to see if the date is in the past.
        # If it is, increment the year by 1.
        today: date = datetime.now().date()
        year: int = today.year
        dt: date = datetime.strptime(f"{d} {str(year)}", "%A %d %B %Y").date()
        if (dt - today) < timedelta(days=-31):
            dt = dt.replace(year=dt.year + 1)
        return dt

    def fetch(self):
        sleep(1)  # prevents test case failures due to query rate

        s = requests.Session()

        # visit homepage to get token for later queries
        r = s.get(
            "https://forms.north-norfolk.gov.uk/xforms/Address/Show/CollectionAddress",
            headers=HEADERS,
        )
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        token: str = soup.find("input", {"name": "__RequestVerificationToken"}).get(
            "value"
        )

        payload: dict = {
            "__RequestVerificationToken": token,
        }

        # use uprn to get address details
        params: dict = {"uprn": self._uprn, "localAddress": "True"}
        r = s.get(
            "https://forms.north-norfolk.gov.uk/xforms/AddressSearch/GetAddressForUprn",
            params=params,
            headers=HEADERS,
        )
        r_json: dict = json.loads(r.content)

        payload.update(
            {
                "SearchPostcode": r_json["postcode"],
                "Address": r_json["uprn"],
                "GisUprn": r_json["uprn"],
                "GisUsrn": r_json["bS7666USRN"],
                "GisTownName": r_json["townName"],
                "GisPostTown": r_json["postTown"],
                "GisPostCode": r_json["postcode"],
                "GisAddress": r_json["locAddress1BS7666"],
                "Address1": "",
                "Address2": "",
                "Address3": "",
                "Address4": "",
                "Postcode": "",
                "LocalSearch": "True",
                "DisableManualEntry": "True",
                "ComponentMode": "False",
                "IsDirty": "True",
            }
        )

        # get collection schedule
        r = s.post(
            "https://forms.north-norfolk.gov.uk/xforms/Address/Show/CollectionAddress",
            headers=HEADERS,
            data=payload,
        )

        entries: list = []

        soup = BeautifulSoup(r.content, "html.parser")
        li: list = soup.find_all("li")
        for item in li:
            details: list = item.find_all("strong")
            entries.append(
                Collection(
                    date=self.append_year(details[2].text),
                    t=str(details[0].text),
                    icon=ICON_MAP.get(details[0].text),
                )
            )

        return entries
