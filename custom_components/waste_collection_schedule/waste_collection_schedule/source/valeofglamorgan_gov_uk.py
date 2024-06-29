import json
import random
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Vale of Glamorgan Council"
DESCRIPTION = "Source for Vale of Glamorgan Council."
URL = "https://valeofglamorgan.gov.uk/"
TEST_CASES = {
    "CF62 7JP": {"uprn": 64003486},
    "CF32 0PW": {"uprn": 64017161},
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Food": "mdi:food",
    "Garden": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

API_URL = "https://myvale.valeofglamorgan.gov.uk/getdata.aspx"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def __get_colltion(self, calendar_url: str, bin_type: str) -> list[Collection]:
        r = requests.get(calendar_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        entries = []
        for tr in soup.select("table tr"):
            tds = tr.select("td")
            if len(tds) != 2:
                continue

            months = tds[0].text.strip()
            days = tds[1].text.strip().replace("and", ",").split(",")
            for day in days:
                day = day.strip()
                if not day.isdigit():
                    continue
                date = datetime.strptime(f"{day} {months}", "%d %B %Y").date()
                entries.append(
                    Collection(date=date, t=bin_type, icon=ICON_MAP[bin_type])
                )
        return entries

    def fetch(self) -> list[Collection]:
        timestamp = str(int(datetime.now().timestamp() * 1000))
        random_callback_number = str(
            random.randint(10000000000000000000, 99999999999999999999)
        )
        params = {
            "RequestType": "LocalInfo",
            "ms": "ValeOfGlamorgan/AllMaps",
            "group": "Waste|new_refuse",
            "type": "jsonp",
            "callback": "AddressInfoCallback",
            "uid": self._uprn,
            "import": f"jQuery{random_callback_number}_{timestamp}",
            "_": timestamp,
        }

        # get json file
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        text = r.text
        text = text.replace("AddressInfoCallback(", "").rstrip(");")
        data = json.loads(text)["Results"]["waste"]

        entries: list[Collection] = []
        recycling_food = data["recycling_food"]
        if recycling_food not in WEEKDAYS:
            raise ValueError(f"Unknown recycling_food: {recycling_food}")

        next_recycling_food = date.today()
        while next_recycling_food.weekday() != WEEKDAYS.index(recycling_food):
            next_recycling_food += timedelta(days=1)

        entries.extend(
            Collection(
                date=next_recycling_food + timedelta(weeks=i),
                t="Recycling",
                icon=ICON_MAP["Recycle"],
            )
            for i in range(10)
        )
        entries.extend(
            Collection(
                date=next_recycling_food + timedelta(weeks=i),
                t="Food",
                icon=ICON_MAP["Food"],
            )
            for i in range(10)
        )

        entries.extend(self.__get_colltion(data["residual_calendar_url"], "Trash"))
        entries.extend(self.__get_colltion(data["green_calendar_url"], "Garden"))

        return entries
