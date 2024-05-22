import base64
import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gateshead Council"
DESCRIPTION = "Source for gateshead.gov.uk services for Gateshead"
URL = "gateshead.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "100000077407"},
    "Test_002": {"uprn": 100000058404},
    "Test_003": {"uprn": 100000033887},
}

ICON_MAP = {
    "Household": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()

        # Start a session
        r = session.get(
            "https://www.gateshead.gov.uk/article/3150/Bin-collection-day-checker"
        )

        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Extract form submission url and form data
        form_url = soup.find("form", attrs={"id": "BINCOLLECTIONCHECKER_FORM"})[
            "action"
        ]
        pageSessionId = soup.find(
            "input", attrs={"name": "BINCOLLECTIONCHECKER_PAGESESSIONID"}
        )["value"]
        sessionId = soup.find(
            "input", attrs={"name": "BINCOLLECTIONCHECKER_SESSIONID"}
        )["value"]
        nonce = soup.find("input", attrs={"name": "BINCOLLECTIONCHECKER_NONCE"})[
            "value"
        ]

        form_data = {
            "BINCOLLECTIONCHECKER_PAGESESSIONID": pageSessionId,
            "BINCOLLECTIONCHECKER_SESSIONID": sessionId,
            "BINCOLLECTIONCHECKER_NONCE": nonce,
            # "BINCOLLECTIONCHECKER_ADDRESSSEARCH_TICKS": ticks,
            "BINCOLLECTIONCHECKER_FORMACTION_NEXT": "BINCOLLECTIONCHECKER_ADDRESSSEARCH_NEXTBUTTON",
            "BINCOLLECTIONCHECKER_ADDRESSSEARCH_UPRN": self._uprn,
            "BINCOLLECTIONCHECKER_ADDRESSSEARCH_ADDRESSTEXT": " ",  # Not quite sure why this is need (can not be empty) maybe used if there are multiple matches=??? But UPRN should be unique???
        }

        # Submit form
        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        # Extract encoded response data
        soup = BeautifulSoup(r.text, features="html.parser")
        pattern = re.compile(
            r"var BINCOLLECTIONCHECKERFormData = \"(.*?)\";$", re.MULTILINE | re.DOTALL
        )
        script = soup.find("script", text=pattern)

        response_data = pattern.search(script.text).group(1)

        # Decode base64 encoded response data and convert to JSON
        decoded_data = base64.b64decode(response_data)
        data = json.loads(decoded_data)
        soup = BeautifulSoup(
            data["HOUSEHOLDCOLLECTIONS_1"]["DISPLAYHOUSEHOLD"], features="html.parser"
        )

        # Extract entries
        entries = []
        month = None
        for tr in soup.find_all("tr"):
            month_th = tr.find("th", attrs={"colspan": "3"})
            if month_th:
                month = month_th.text.split(" ")[
                    0
                ]  # split if month is followed by year (may happen in December, not sure)
                continue
            if not month:
                continue

            tds = tr.find_all("td")
            if len(tds) != 3:
                continue
            day = tds[0].text
            types = tds[2].text.split(" and ")

            now = datetime.now()
            dt = datetime.strptime(f"{now.year}-{month}-{day}", "%Y-%B-%d").date()
            if dt.month in (1, 2, 3) and now.month in (
                11,
                12,
            ):  # fix Dates for next year
                dt = dt.replace(year=now.year + 1)
            for type in types:
                entries.append(
                    Collection(
                        date=dt,
                        t=type.strip(),
                        icon=ICON_MAP.get(type),
                    )
                )

        return entries
