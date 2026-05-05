import logging
from datetime import date, datetime, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Swale Borough Council"
DESCRIPTION = "Source for swale.gov.uk services for Swale, UK."
URL = "https://swale.gov.uk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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

        # mimic postcode search
        payload: dict = {
            "SQ_FORM_499078_PAGE": "1",
            "form_email_499078_referral_url": "https://swale.gov.uk/bins-littering-and-the-environment/bins",
            "q499089:q1": self._postcode,
            "form_email_499078_submit": "Choose Your Address &#10140;",
        }
        r = s.post(
            "https://swale.gov.uk/bins-littering-and-the-environment/bins/check-your-bin-day",
            headers=HEADERS,
            data=payload,
        )
        r.raise_for_status()
        sleep(5)

        # mimic address selection
        payload = {
            "SQ_FORM_499078_PAGE": "2",
            "form_email_499078_referral_url": "https://swale.gov.uk/bins-littering-and-the-environment/bins",
            "q499093:q1": self._uprn,
            "form_email_499078_submit": "Get Bin Days &#10140;",
        }
        r = s.post(
            "https://swale.gov.uk/bins-littering-and-the-environment/bins/check-your-bin-day",
            headers=HEADERS,
            data=payload,
        )
        r.raise_for_status()
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        temp_list: list = []

        # Get details of next collection
        next_date = soup.find("strong", {"id": "SBC-YBD-collectionDate"})
        if not next_date:
            raise ValueError(
                "Could not find next collection date — the page may have changed or returned an error."
            )

        waste_list = soup.find("div", {"id": "SBCFirstBins"})
        if not waste_list:
            raise ValueError(
                "Could not find waste list — the page may have changed or returned an error."
            )
        waste_items = waste_list.find_all("li")

        # Determine actual date from the text
        raw_date = next_date.text.lower()

        if "today" in raw_date:
            dt = datetime.today().strftime("%d %B %Y")
        elif "tomorrow" in raw_date:
            dt = (datetime.today() + timedelta(days=1)).strftime("%d %B %Y")
        else:
            # Try to extract actual date from string like "Tuesday, 14 April 2025"
            try:
                # Remove the weekday part, e.g., "Monday, "
                dt = raw_date.split("y, ")[
                    -1
                ].strip()  # This might still not work for all formats
            except IndexError:
                dt = "Unknown"

        for item in waste_items:
            temp_list.append(
                [
                    dt,
                    item.text.strip(),
                ]
            )

        # get details of future collection
        future_collection = soup.find("div", {"id": "FutureCollections"})
        if not future_collection:
            raise ValueError(
                "Could not find future collections — the page may have changed or returned an error."
            )

        future_date = future_collection.find("p")
        if not future_date:
            raise ValueError(
                "Could not find future collection date — the page may have changed or returned an error."
            )

        future_list = soup.find("ul", {"id": "FirstFutureBins"})
        if not future_list:
            raise ValueError(
                "Could not find future bins list — the page may have changed or returned an error."
            )

        future_items = future_list.find_all("li")
        for item in future_items:
            dt = future_date.text.split("y, ")[-1]
            temp_list.append(
                [
                    dt,
                    item.text.strip(),
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
            raw = pickup[1].strip().lower()
            waste_type = remap_wastes.get(raw)
            if waste_type is None:
                _LOGGER.warning("Unknown waste type '%s' — skipping", raw)
                continue
            entries.append(
                Collection(
                    date=waste_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
