import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mid-Sussex District Council"
DESCRIPTION = (
    "Source for midsussex.gov.uk services for Mid-Sussex District Council, UK."
)
URL = "https://midsussex.gov.uk"

TEST_CASES = {
    "Test_001": {"house_number": "6", "street": "Withypitts", "postcode": "RH10 4PJ"},
    "Test_002": {
        "house_name": "Oaklands",
        "street": "Oaklands Road",
        "postcode": "RH16 1SS",
    },
    "Test_003": {"house_number": 9, "street": "Bolnore Road", "postcode": "RH16 4AB"},
    "Test_004": {"address": "HAZELMERE REST HOME, 21 BOLNORE ROAD RH16 4AB"},
}

ICON_MAP = {
    "Garden bin collection": "mdi:leaf",
    "Rubbish bin collection": "mdi:trash-can",
    "Recycling bin collection": "mdi:recycle",
}

API_URL = "https://www.midsussex.gov.uk/waste-recycling/bin-collection/"
REGEX = r"([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})"  # regex for UK postcode format


class Source:
    def __init__(
        self, house_name="", house_number="", street="", postcode="", address=""
    ):
        self._house_name = str(house_name).upper()
        self._house_number = str(house_number)
        self._street = str(street).upper()
        self._postcode = str(postcode).upper()
        self._address = str(address).upper()

    def fetch(self):
        s = requests.Session()

        if self._address != "":
            # extract postcode
            self._postcode = re.findall(REGEX, self._address)
        elif self._house_name == "":
            self._address = (
                self._house_number + " " + self._street + " " + self._postcode
            )
        else:
            self._address = (
                self._house_name
                + ","
                + self._house_number
                + " "
                + self._street
                + " "
                + self._postcode
            )

        r0 = s.get(API_URL)
        soup = BeautifulSoup(r0.text, features="html.parser")

        payload = {
            "__RequestVerificationToken": soup.find(
                "input", {"name": "__RequestVerificationToken"}
            ).get("value"),
            "ufprt": soup.find("input", {"name": "ufprt"}).get("value"),
            "StrPostcodeSearch": self._postcode,
            "StrAddressSelect": self._address,
            "Next": "true",
            "StepIndex": "1",
        }

        # Seems to need a ufprt, so get that and then repeat query
        r1 = s.post(API_URL, data=payload)

        soup = BeautifulSoup(r1.text, features="html.parser")
        ufprt = soup.find("input", {"name": "ufprt"}).get("value")
        token = soup.find("input", {"name": "__RequestVerificationToken"}).get("value")
        payload.update({"ufprt": ufprt, "__RequestVerificationToken": token})

        # Retrieve collection details
        r2 = s.post(API_URL, data=payload)
        soup = BeautifulSoup(r2.text, features="html.parser")
        table = soup.find("table", {"class": "collDates"})
        trs = table.findAll("tr")[1:]  # remove header row

        entries: list[Collection] = []

        for tr in trs:
            td = tr.findAll("td")[1:]
            entries.append(
                Collection(
                    date=datetime.strptime(td[1].text, "%A %d %B %Y").date(),
                    t=td[0].text,
                    icon=ICON_MAP.get(td[0].text),
                )
            )

        # Check for Christmas changes
        christms_heading = soup.find(
            "strong", text=re.compile("Christmas Bin Collection Calendar")
        )

        if not christms_heading:
            return entries
        try:
            xmas_trs = christms_heading.findParent("table").findAll("tr")[1:]
        except Exception:
            return entries

        for tr in xmas_trs:
            tds = tr.findAll("td")
            try:
                normal_date = datetime.strptime(tds[0].text.strip(), "%A %d %B").date()
                fetive_date = datetime.strptime(tds[1].text.strip(), "%A %d %B").date()
            except Exception:
                continue
            for entry in entries.copy():
                date = entry.date
                if date.month == normal_date.month and date.day == normal_date.day:
                    entries.remove(entry)
                    entries.append(
                        Collection(
                            date=fetive_date.replace(year=date.year),
                            t=entry.type,
                            icon=entry.icon,
                        )
                    )
                    break
        return entries
