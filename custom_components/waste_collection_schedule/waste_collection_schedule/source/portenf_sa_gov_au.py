import logging
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
# These two lines areused to suppress the InsecureRequestWarning when using verify=False
urllib3.disable_warnings()

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
    "general-waste bin": "mdi:trash-can",
    "organics bin": "mdi:leaf",
    "recycling bin": "mdi:recycle",
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
        self, soup: BeautifulSoup, event_taget=None, additional: dict = {}
    ) -> dict:
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

        # extractt arguments
        args = self.__set_args(
            BeautifulSoup(r.text, "html.parser"),
            event_taget="ctl00$MainContent$btnSearch",
        )

        r = session.post(API_URL, data=args)
        r.raise_for_status()

        # get page to select an address
        soup = BeautifulSoup(r.text, "html.parser")

        selectable = soup.find_all("a", {"class": "anchor-button small"}, text="Select")

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
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        cal_header = soup.find("th", {"class": "header-month"}).find("span").text

        from_month = cal_header.split("-")[0].strip()
        to_month = cal_header.split("-")[1].strip().split(" ")[0]
        to_year = from_year = cal_header.split("-")[1].strip().split(" ")[1]
        # if main month contains a year, set it (maybe happens in december???)
        if len(from_month.split(" ")) > 1:
            from_year = from_month.split(" ")[1]
            from_month = from_month.split(" ")[0]

        today_div = soup.find("table", id="cal").find("td", class_="today")
        print(today_div)

        # if other-month is to_month
        if (
            "other-month" in today_div.attrs
            and datetime.now().strftime("%B") != to_month
        ):
            main_month, other_month = from_month, to_month
            main_year, other_year = from_year, to_year
        else:  # if other-month is from_month
            main_month, other_month = to_month, from_month
            main_year, other_year = to_year, from_year

        entries = []

        calendar = soup.find("table", {"class": "collection-day-calendar"})
        # Iterate over all days with pickups
        for pickup in calendar.find_all(
            "div", {"class": re.compile(r"pickup|next-pickup")}
        ):
            parent_td = pickup.parent
            month = (
                main_month if "main-month" in parent_td.attrs["class"] else other_month
            )
            year = main_year if "main-month" in parent_td.attrs["class"] else other_year
            day = parent_td.find("div", {"class": "daynumber"}).text

            # Iterate over all pickup container types for this day
            for container in pickup.find_all("div", {"class": "bin-container"}):
                container_type = " ".join(container.find("div").attrs["class"])
                container_icon = ICON_MAP.get(container_type)

                date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%B-%d").date()
                entries.append(
                    Collection(date=date, t=container_type, icon=container_icon)
                )

        return entries
