# import json
# import re

from datetime import date, datetime, timedelta
from time import sleep as sleep

import requests
from bs4 import BeautifulSoup

# from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Swale Borough Council"
DESCRIPTION = "Source for swale.gov.uk services for Swale, UK."
URL = "https://swale.gov.uk"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
}
API_URL = (
    "https://swale.gov.uk/bins-littering-and-the-environment/bins/my-collection-day"
)
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food-apple",
    "Garden": "mdi:leaf",
}
# swale.gov.uk has an aggressive limit of request frequency,
# running test cases can result in the error: 429 Too Many Requests.
# Shouldn't be an issue in normal use unless HA is restarted frequently.
TEST_CASES = {
    "Swale House": {"uprn": 100062375927, "postcode": "ME10 3HT"},
    "1 Harrier Drive": {"uprn": 100061091726, "postcode": "ME10 4UY"},
    "garden waste test": {"uprn": "200002536346", "postcode": "ME10 1YQ"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
        "postcode": "Postcode of the property",
    },
}

# DATE_KEYS = {
#     "NextDateUTC",
#     "FollowingDateUTC",
#     "Following2DateUTC",
#     "Following3DateUTC",
# }


class Source:
    def __init__(self, uprn: int | str, postcode: str):
        self._uprn: str = str(uprn)
        self._postcode: str = postcode

    def append_year(self, d: str) -> date:
        # Website doesn't return the year.
        # Append the current year, and then check to see if the date is in the past.
        # If it is, increment the year by 1.
        today: date = datetime.now().date()
        year: int = today.year
        dt: date = datetime.strptime(f"{d} {str(year)}", "%d %B %Y").date()
        if (dt - today) < timedelta(days=-31):
            dt = dt.replace(year=dt.year + 1)
        return dt

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # mimic postocde search
        payload: dict = {
            "SQ_FORM_485465_PAGE": "1",
            "form_email_485465_referral_url": "https://swale.gov.uk/bins-littering-and-the-environment/bins",
            "q485476:q1": self._postcode,
            "form_email_485465_submit": "Choose Your Address &#10140;",
        }
        r = s.post(
            "https://swale.gov.uk/bins-littering-and-the-environment/bins/check-your-bin-day",
            headers=HEADERS,
            data=payload,
        )
        r.raise_for_status
        sleep(5)

        # mimic address selection
        payload = {
            "SQ_FORM_485465_PAGE": "2",
            "form_email_485465_referral_url": "https://swale.gov.uk/bins-littering-and-the-environment/bins",
            "q485480:q1": self._uprn,
            "form_email_485465_submit": "Get Bin Days &#10140;",
        }
        r = s.post(
            "https://swale.gov.uk/bins-littering-and-the-environment/bins/check-your-bin-day",
            headers=HEADERS,
            data=payload,
        )
        r.raise_for_status
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        temp_list: list = []

        # get  details of next collection
        next_date = soup.find("strong", {"id": "SBC-YBD-collectionDate"})
        waste_list = soup.find("div", {"id": "SBCFirstBins"})
        waste_items = waste_list.find_all("li")
        for item in waste_items:
            dt: str = next_date.text.split("y, ")[-1]
            temp_list.append(
                [
                    dt,
                    item.text,
                ],
            )

        # get details of future collection
        future_collection = soup.find("div", {"id": "FutureCollections"})
        future_date = future_collection.find("p")
        future_list = soup.find("ul", {"id": "FirstFutureBins"})
        future_items = future_list.find_all("li")
        for item in future_items:
            dt = future_date.text.split("y, ")[-1]
            temp_list.append(
                [
                    dt,
                    item.text,
                ],
            )

        # remap new waste descriptions to old icon map descriptions for backwards compatibility
        remap_wastes: dict = {
            "blue bin": "Recycling",
            "food waste": "Food",
            "green bin": "Refuse",
            "garden waste": "Garden",
        }

        # build collection schedule
        entries: list = []
        for pickup in temp_list:
            waste_date: date = self.append_year(pickup[0])
            waste_type: str = remap_wastes[pickup[1]]
            entries.append(
                Collection(
                    date=waste_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        # collection_soup = BeautifulSoup(collection_response.text, "html.parser")

        # # get details of next collection
        # next_date = collection_soup.find("strong", {"id": "SBC-YBD-collectionDate"})
        # next_wastes = collection_soup.find("div", {"id": "SBCFirstBins"})
        # next_items = next_wastes.find_all("li")
        # print(next_date, next_items)

        # # get details of future collection
        # future_collection = collection_soup.find("div", {"id": "FutureCollections"})
        # future_date = future_collection.text.split(", ")[-1]
        # future_wastes = collection_soup.find("ul", {"id": "FirstFutureBins"})
        # future_items = future_wastes.find_all("li")
        # print(future_date, future_items)

        # section = collection_soup.find("section", id="SBC-YBD-collectionDate")
        # if not section:
        #     raise ValueError(
        #         "Could not find SBC-YBD_main section. Most likely html has changed"
        #     )
        # script = section.find("script", recursive=False)
        # if not script:
        #     raise ValueError(
        #         "Could not find script entry. Most likely html has changed"
        #     )

        # bin_data = re.search(
        #     r"var BIN_DAYS = Object\.entries\(JSON\.parse\('(.+)'\)\);", script.string
        # )
        # if not bin_data:
        #     raise ValueError(
        #         "Could not find BIN_DAYS in response. Most likely html has changed"
        #     )
        # bin_days = json.loads(bin_data.group(1))
        # for bin in bin_days:
        #     bin_details = bin_days[bin]
        #     if bin_details["Active"] == "Y":
        #         for dateKey in DATE_KEYS:
        #             if dateKey in bin_details:
        #                 entries.append(
        #                     Collection(
        #                         date=parse(bin_details[dateKey]).date(),
        #                         t=bin,
        #                         icon=ICON_MAP.get(bin),
        #                     )
        #                 )
        # if not entries:
        #     raise ValueError(
        #         "Could not get collections for the given combination of UPRN and Postcode."
        #     )
        return entries
