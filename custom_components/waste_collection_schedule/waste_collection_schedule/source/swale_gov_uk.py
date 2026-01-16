from datetime import date, datetime, timedelta
from time import sleep as sleep

import requests
from bs4 import BeautifulSoup
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
        r.raise_for_status
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
        r.raise_for_status
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        temp_list: list = []

        # Get details of next collection
        next_date = soup.find("strong", {"id": "SBC-YBD-collectionDate"})
        waste_list = soup.find("div", {"id": "SBCFirstBins"})
        waste_items = waste_list.find_all("li")

        # Determine actual date from the text
        raw_date = next_date.text.lower()

        if "today" in raw_date:
            dt = datetime.today().strftime("%d %B")
        elif "tomorrow" in raw_date:
            dt = (datetime.today() + timedelta(days=1)).strftime("%d %B")
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

        return entries
