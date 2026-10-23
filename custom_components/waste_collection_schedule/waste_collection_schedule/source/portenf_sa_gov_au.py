import logging
from datetime import date, datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


TITLE = "Port Adelaide Enfield, South Australia"
DESCRIPTION = "Source for City of Port Adelaide Enfield, South Australia."
URL = "https://ecouncil.portenf.sa.gov.au/"
TEST_CASES = {
    "Broadview, Regency Road, 565 ": {
        "suburb": "Broadview",
        "street": "Regency Road",
        "house_number": 565,
        "unit_number": "",
    },
    "48 Floriedale Rd ": {
        "suburb": "Greenacres",
        "street": "Floriedale Rd",
        "house_number": "48",
    },
    "24 Margaret Terrace": {
        "suburb": "Rosewater",
        "street": "Margaret Terrace",
        "house_number": "24",
    },
    "Addison Road 91 with unit": {
        "suburb": "Rosewater",
        "street": "Addison Road",
        "house_number": 91,
        "unit_number": 2,
    },
}

ICON_MAP = {
    "general-waste bin": Icons.GENERAL_WASTE,
    "organics bin": Icons.ORGANIC,
    "recycling bin": Icons.RECYCLING,
}

LOGGER = logging.getLogger(__name__)

API_URL = "https://ecouncil.portenf.sa.gov.au/public/propertywastedates/public.aspx"


class Source:
    def __init__(
        self,
        suburb: str,
        street: str,
        house_number: str | int,
        unit_number: str | int = "",
    ):
        self._suburb: str = suburb
        self._street: str = street
        self._house_number: str = str(house_number)
        self._unit_number: str = str(unit_number)

    def __set_args(
        self, soup: BeautifulSoup, event_taget=None, additional: dict | None = None
    ) -> dict:
        if additional is None:
            additional = {}
        args = {
            "ctl00$MainContent$txtSuburb": self._suburb,
            "ctl00$MainContent$txtStreetName": self._street,
            "ctl00$MainContent$txtHouseNumber": self._house_number,
            "ctl00$MainContent$txtUnitNumber": self._unit_number,
        }
        if event_taget is not None:
            args["__EVENTTARGET"] = event_taget

        for hidden_val in soup.find_all("input", {"type": "hidden"}):
            args[hidden_val["name"]] = hidden_val["value"]

        for key, value in additional.items():
            args[key] = value
        return args

    def fetch(self):
        session = requests.Session()

        # get First page
        r = session.get(API_URL, verify=False)
        r.raise_for_status()

        # extract arguments
        args = self.__set_args(
            BeautifulSoup(r.text, "html.parser"),
            event_taget="ctl00$MainContent$btnSearch",
        )

        r = session.post(API_URL, data=args, verify=False)
        r.raise_for_status()

        # get page to select an address
        soup = BeautifulSoup(r.text, "html.parser")

        selectable = soup.find_all(
            "a", {"class": "anchor-button small"}, string="Select"
        )

        if len(selectable) == 0:
            raise ValueError("No address found")
        selected = selectable[0]

        # If multiple addresses are found, try to find the one that matches the input and warn if there are multiple or none matches
        if len(selectable) > 1:
            found = [
                " ".join(
                    [y.text for y in x.parent.parent.find_all("td")[1].find_all("span")]
                )
                for x in selectable
            ]
            using_index = 0

            match = False

            for index, entry in enumerate(found):
                entry = entry.lower().strip().replace("  ", "")
                if (
                    self._house_number.lower().strip().replace("  ", "") in entry
                    and self._street.lower().strip().replace("  ", "") in entry
                    and self._suburb.lower().strip().replace("  ", "") in entry
                    and self._unit_number.lower().strip().replace("  ", "") in entry
                ):
                    if match:
                        LOGGER.warning(
                            f"Multiple addresses found, using first one \nfound:{', '.join(found[:10])}{'...' if len(found) >= 10 else ''} \nusing:{found[using_index]}"
                        )
                        break
                    using_index = index
                    match = True
            if not match:
                LOGGER.warning(
                    f"no perfect address match found, using:{found[using_index]}"
                )

        # request first address
        args = self.__set_args(
            soup,
            event_taget="ctl00$MainContent$gvPropertyResults$ctl02$btnSelect",
            additional={selected["href"].split("'")[1]: ""},
        )
        r = session.post(API_URL, data=args, verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        calendar = soup.find("table", {"class": "collection-day-calendar"})
        if calendar is None:
            raise ValueError("Collection calendar not found")
        header = calendar.find("th", {"class": "header-month"})
        if header is None:
            raise ValueError("Collection calendar header not found")

        month_range = header.get_text(" ", strip=True).split("-")
        start = month_range[0].split()
        month = datetime.strptime(start[0], "%B").month
        if len(start) > 1:
            year = int(start[1])
        elif len(month_range) > 1:
            end_month, end_year = month_range[-1].split()
            year = int(end_year)
            if month > datetime.strptime(end_month, "%B").month:
                year -= 1
        else:
            # single-month header with no year -> current year
            year = datetime.now().year

        entries = []
        previous_day = None

        # Use day order instead of "today" marker
        for cell in calendar.find_all("td"):
            day_number = cell.find("div", class_=["daynumber", "daynumber-empty"])
            if day_number is None:
                raise ValueError("Collection calendar day number not found")
            day = int(day_number.get_text(strip=True))
            if previous_day is not None and day < previous_day:
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
            previous_day = day
            collection_date = date(year, month, day)

            pickup = cell.find("div", class_=["pickup", "next-pickup"])
            if pickup is None:
                continue

            # Iterate over all pickup container types for this day
            for container in pickup.find_all("div", {"class": "bin-container"}):
                container_type = " ".join(container.find("div").attrs["class"])
                container_icon = ICON_MAP.get(container_type)

                entries.append(
                    Collection(
                        date=collection_date, t=container_type, icon=container_icon
                    )
                )

        if previous_day is None:
            raise ValueError("Collection calendar contains no days")

        return entries
