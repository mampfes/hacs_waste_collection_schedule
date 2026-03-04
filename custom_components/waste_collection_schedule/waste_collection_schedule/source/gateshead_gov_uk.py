import base64
import binascii
import json
import re
from datetime import datetime

import cloudscraper
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
        session = cloudscraper.create_scraper()

        r = session.get(
            "https://www.gateshead.gov.uk/article/3150/Bin-collection-day-checker",
            timeout=30,
        )

        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        form = soup.find("form", attrs={"id": "BINCOLLECTIONCHECKER_FORM"})
        if not form or "action" not in form.attrs:
            raise ValueError("Could not find form or form action")
        form_url = form["action"]

        pageSessionId_input = soup.find(
            "input", attrs={"name": "BINCOLLECTIONCHECKER_PAGESESSIONID"}
        )
        if not pageSessionId_input or "value" not in pageSessionId_input.attrs:
            raise ValueError("Could not find BINCOLLECTIONCHECKER_PAGESESSIONID")
        pageSessionId = pageSessionId_input["value"]

        sessionId_input = soup.find(
            "input", attrs={"name": "BINCOLLECTIONCHECKER_SESSIONID"}
        )
        if not sessionId_input or "value" not in sessionId_input.attrs:
            raise ValueError("Could not find BINCOLLECTIONCHECKER_SESSIONID")
        sessionId = sessionId_input["value"]

        nonce_input = soup.find("input", attrs={"name": "BINCOLLECTIONCHECKER_NONCE"})
        if not nonce_input or "value" not in nonce_input.attrs:
            raise ValueError("Could not find BINCOLLECTIONCHECKER_NONCE")
        nonce = nonce_input["value"]

        form_data = {
            "BINCOLLECTIONCHECKER_PAGESESSIONID": pageSessionId,
            "BINCOLLECTIONCHECKER_SESSIONID": sessionId,
            "BINCOLLECTIONCHECKER_NONCE": nonce,
            "BINCOLLECTIONCHECKER_FORMACTION_NEXT": "BINCOLLECTIONCHECKER_ADDRESSSEARCH_NEXTBUTTON",
            "BINCOLLECTIONCHECKER_ADDRESSSEARCH_UPRN": self._uprn,
            "BINCOLLECTIONCHECKER_ADDRESSSEARCH_ADDRESSTEXT": " ",
        }

        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        pattern = re.compile(
            r"var BINCOLLECTIONCHECKERFormData = \"(.*?)\";$", re.MULTILINE | re.DOTALL
        )
        script = soup.find("script", string=pattern)

        if not script:
            raise ValueError("Could not find BINCOLLECTIONCHECKERFormData in response")

        match = pattern.search(script.text)
        if not match:
            raise ValueError("Could not extract BINCOLLECTIONCHECKERFormData value")
        response_data = match.group(1)

        try:
            decoded_data = base64.b64decode(response_data)
            data = json.loads(decoded_data)
        except (binascii.Error, ValueError) as e:
            raise ValueError(f"Failed to decode base64 data: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON data: {e}")

        if "HOUSEHOLDCOLLECTIONS_1" not in data:
            raise ValueError("HOUSEHOLDCOLLECTIONS_1 not found in response data")
        if "DISPLAYHOUSEHOLD" not in data["HOUSEHOLDCOLLECTIONS_1"]:
            raise ValueError("DISPLAYHOUSEHOLD not found in response data")

        soup = BeautifulSoup(
            data["HOUSEHOLDCOLLECTIONS_1"]["DISPLAYHOUSEHOLD"], features="html.parser"
        )

        entries = []
        month = None
        for tr in soup.find_all("tr"):
            month_th = tr.find("th", attrs={"colspan": "3"})
            if month_th:
                month = month_th.text.split(" ")[0]
                continue
            if not month:
                continue

            tds = tr.find_all("td")
            if len(tds) != 3:
                continue
            day = tds[0].text.strip()
            waste_types = tds[2].text.split(" and ")

            now = datetime.now()
            month_capitalized = month.capitalize()
            try:
                dt = datetime.strptime(
                    f"{now.year}-{month_capitalized}-{day}", "%Y-%B-%d"
                ).date()
            except ValueError:
                day_clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", day)
                dt = datetime.strptime(
                    f"{now.year}-{month_capitalized}-{day_clean}", "%Y-%B-%d"
                ).date()

            if dt.month in (1, 2, 3) and now.month in (11, 12):
                dt = dt.replace(year=now.year + 1)
            elif dt.month == 12 and now.month in (1, 2, 3):
                dt = dt.replace(year=now.year - 1)
            elif dt < now.date() and (now.date() - dt).days > 180:
                dt = dt.replace(year=now.year + 1)

            day_change_regex = re.compile(
                r"(.*?)\s*-?\s*DAY CHANGE\s*$", re.IGNORECASE | re.DOTALL
            )
            for waste_type in waste_types:
                day_change_match = day_change_regex.match(waste_type)

                if day_change_match:
                    waste_type = day_change_match.group(1)
                entries.append(
                    Collection(
                        date=dt,
                        t=waste_type.strip(),
                        icon=ICON_MAP.get(waste_type.strip()),
                    )
                )

        return entries
