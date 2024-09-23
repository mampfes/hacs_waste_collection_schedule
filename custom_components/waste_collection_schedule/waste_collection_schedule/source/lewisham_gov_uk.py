import datetime
import logging
import re

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "London Borough of Lewisham"
DESCRIPTION = "Source for services from the London Borough of Lewisham"
URL = "https://lewisham.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "SE41LR", "number": 4},
    "houseName": {"post_code": "SE233TE", "name": "The Haven"},
    "houseUprn": {"uprn": "10070495030"},
    "houseUprn2": {"uprn": 100021959032},
}

BASE_URL = "https://lewisham.gov.uk"
ADDRESS_SEARCH_URL = "https://lewisham.gov.uk/api/AddressFinder"


DATE_REGEX = r"(\d{2}/\d{2}/\d{4})"
DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

ICON_MAP = {
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "food": "mdi:food-apple",
    "garden": "mdi:leaf",
}

ID_SEPERATOR = "-----------------------------{rand_id}"
PAYLOAD_SECTION_TEMPLATE = (
    ID_SEPERATOR
    + """
Content-Disposition: form-data; name="{name}"

{value}
"""
)


class InsufficientDataError(Exception):
    pass


class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number
        self._name = name
        self._uprn = uprn

    def get_uprn(self) -> None:
        if not self._uprn:
            # look up the UPRN for the address
            p = {"postcodeOrStreet": self._post_code}
            r = requests.post(ADDRESS_SEARCH_URL, params=p)
            r.raise_for_status()
            addresses = r.json()

            if self._name:
                self._uprn = [
                    x["Uprn"]
                    for x in addresses
                    if (x["Title"]).upper().startswith(self._name.upper())
                ][0]
            elif self._number:
                self._uprn = [
                    x["Uprn"]
                    for x in addresses
                    if (x["Title"]).startswith(str(self._number))
                ][0]

            if not self._uprn:
                raise Exception(
                    f"Could not find address {self._post_code} {self._number}{self._name}"
                )

    def fetch(self) -> list[Collection]:
        if not self._uprn:
            self.get_uprn()
        s = requests.Session()

        r = s.get(
            "https://lewisham.gov.uk/myservices/recycling-and-rubbish/your-bins/collection"
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form_div = soup.find("div", {"class": "address-finder"})
        if not isinstance(form_div, Tag):
            raise Exception("Could not find address form")

        form = form_div.find_parent("form")
        if not isinstance(form_div, Tag):
            raise Exception("Could not find address form")

        action = form.get("action")
        if not action:
            raise Exception("Could not find form action")
        if action.startswith("/"):
            action = BASE_URL + action

        inputs = form.find_all("input")
        rand_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f%f%H%m")

        payload = ""
        for input in inputs:
            name = input.get("name")
            value = input.get("value")
            if name:
                if name.endswith("Value"):
                    value = self._uprn
                payload += PAYLOAD_SECTION_TEMPLATE.format(
                    rand_id=rand_id, name=name, value=value
                )

        payload += ID_SEPERATOR.format(rand_id=rand_id) + "--"
        headers = {
            "Content-Type": f"multipart/form-data; boundary=---------------------------{rand_id}",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
        }

        r = s.post(action, data=payload, headers=headers)
        r.raise_for_status()

        url = r.text.split("='")[-1].split("';")[0]
        if not url:
            raise Exception("Could not find collection URL")
        if url.startswith("/"):
            url = BASE_URL + url

        r = s.get(url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        heading = soup.find("h2", text="When your bins are collected:")
        if not heading:
            raise Exception("Could not find collection heading")

        entries: list[Collection] = []
        waste_type: str | None = None
        frequency: str | None = None
        week_day: str | None = None
        date: datetime.date | None = None
        for sibling in heading.parent.contents:
            if sibling.name == "strong":
                if waste_type is not None:
                    try:
                        entries.extend(
                            self._calculate_collections(
                                waste_type, frequency, week_day, date
                            )
                        )
                    except InsufficientDataError as e:
                        _LOGGER.warning(
                            f"Could not calculate collection got exception: {e}"
                        )
                    waste_type = None
                    frequency = None
                    week_day = None
                    date = None

                waste_type = sibling.text.strip()
            if sibling.name == "span":
                frequency = sibling.text
            if sibling.name is None:
                for day in DAYS:
                    if day.lower() in sibling.text.lower():
                        week_day = day
                        break
                if result := re.search(DATE_REGEX, sibling.text):
                    date = datetime.datetime.strptime(
                        result.group(1), "%d/%m/%Y"
                    ).date()

        try:
            entries.extend(
                self._calculate_collections(waste_type, frequency, week_day, date)
            )
        except InsufficientDataError as e:
            _LOGGER.warning(f"Could not calculate collection got exception: {e}")

        return entries

    def _calculate_collections(
        self,
        waste_type: str | None,
        frequency: str | None,
        week_day: str | None,
        date: datetime.date | None,
    ) -> list[Collection]:
        if waste_type is None:
            raise InsufficientDataError("Waste type not provided")

        if frequency not in ("WEEKLY", "FORTNIGHTLY"):
            raise InsufficientDataError("Frequency not provided")
        if week_day is None:
            raise InsufficientDataError("Week day not provided")
        if frequency == "FORTNIGHTLY" and date is None:
            raise InsufficientDataError("Date not provided")

        entries = []

        collection_dates: list[datetime.date] = []
        if date is None:
            d = datetime.date.today()
            date = d + datetime.timedelta(
                (DAYS.index(week_day.upper()) + 1 - d.isoweekday()) % 7
            )
        if frequency == "FORTNIGHTLY":
            collection_dates = [date + datetime.timedelta(i * 14) for i in range(5)]
        else:
            collection_dates = [date + datetime.timedelta(i * 7) for i in range(10)]
        for collection_date in collection_dates:
            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.split()[0].lower()),
                )
            )

        return entries
