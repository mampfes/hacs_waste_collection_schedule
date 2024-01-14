import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Greater Geelong"
DESCRIPTION = "Source City of Greater Geelong rubbish collection"
URL = "https://www.geelongaustralia.com.au/"
TEST_CASES = {
    "155 Mercer Street Geelong 3220": {"address": "155 Mercer Street Geelong 3220"},
    "1/271 Roslyn Road Highton 3216": {"address": "1/271 Roslyn Road Highton 3216"},
    "1a Orton Street Ocean Grove 3226": {"address": "1a Orton Street Ocean Grove 3226"},
    "100-102 Gheringhap Street Geelong 3220": {
        "address": "100-102 Gheringhap Street Geelong 3220"
    },
}

API_URL = "https://www.geelongaustralia.com.au/recycling/calendar/default.aspx"
ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green waste": "mdi:leaf",
}

SUBMIT_ARGS = {
    "ctl00$ContentBody$BTN_SEARCH": "Search",
}

ADDRESS_FIELD = "ctl00$ContentBody$TB_SEARCH"


class Source:
    def __init__(
        self, address: str
    ):  # argX correspond to the args dict in the source configuration
        self._address = address
        self._submit_args = SUBMIT_ARGS.copy()
        self._submit_args[ADDRESS_FIELD] = f"{self._address}"

    def fetch(self):
        s = requests.Session()
        r = s.get(API_URL)
        r.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")

        viewstate = soup.find("input", id="__VIEWSTATE")
        eventvalidation = soup.find("input", id="__EVENTVALIDATION")

        if (
            not viewstate
            or not isinstance(viewstate, Tag)
            or not eventvalidation
            or not isinstance(eventvalidation, Tag)
        ):
            raise Exception("could not get valid data from geelongaustralia.com.au")

        self._submit_args["__VIEWSTATE"] = str(viewstate["value"])

        self._submit_args["__EVENTVALIDATION"] = str(eventvalidation["value"])

        r = requests.post(API_URL, data=self._submit_args)
        r.raise_for_status()

        if "We couldn't find a match for" in r.text:
            raise Exception(
                f"No collection calendars are available for the selected property. Make sure your address returns entries on the council website ({API_URL})."
            )

        soup = BeautifulSoup(r.text, "html.parser")

        div = soup.find("div", id="ctl00_ContentBody_P_CALENDAR").find(
            "div", class_="read-text"
        )

        bins = div.find_all("h3", class_="heading-icon")
        next4s = div.find_all("ul")
        entries = []  # List that holds collection schedule

        for bin, next4 in zip(bins, next4s):
            t = bin.text.split(" (", 1)[0]
            dates = next4.find_all("li")
            for date in dates:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(
                            date.text, "%A, %d %B %Y"
                        ).date(),
                        t=t,  # Collection type
                        icon=ICON_MAP.get(t),  # Collection icon
                    )
                )

        return entries
