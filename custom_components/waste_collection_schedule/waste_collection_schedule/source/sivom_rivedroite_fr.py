import json
import re
from datetime import date

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection

FRENSH_WEEKDAYS = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}

TITLE = "Sivom Rive Droite - Bassens"
DESCRIPTION = "Source for Sivom Rive Droite."
URL = "https://www.sivom-rivedroite.fr/"
TEST_CASES = {
    "BASSENS 3": {"district": "BASSENS 3"},
    "BASSENS 1": {"district": "BASSENS 1 et BASSENS 2"},
}


ICON_MAP = {
    "Ménagères": "mdi:trash-can",
    "Recyclables": "mdi:recycle",
}


API_URL = "https://www.google.com/maps/d/embed?mid=192kaU1tycR1QLrQuF_1hhIdtwghc1GDg&ll=44.90521499253571,-0.5239428999999873&z=13"
PAGE_DATA_REGEX = r'var _pageData\s+=\s*"(\[.*?\])";'


class Source:
    def __init__(self, district: str):
        self._district: str = district

    def get_descriptions(self, data) -> dict[str, str]:
        to_return: dict[str, str] = {}
        if isinstance(data, list):
            if len(data) == 0:
                return to_return
            if (
                len(data) > 1
                and isinstance(data[0], list)
                and isinstance(data[1], list)
                and len(data[0]) != 0
                and len(data[1]) != 0
                and data[0][0] == "nom"
                and data[1][0] == "description"
            ):
                to_return = {data[0][1][0].lower(): data[1][1][0]}
                for nom in data[0][1][0].lower().split(" et "):
                    to_return.update(
                        {d: data[1][1][0] for d in data[0][1][0].lower().split(" et ")}
                    )

            for d in data:
                to_return.update(self.get_descriptions(d))
        return to_return

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL)

        r.raise_for_status()
        r.encoding = "utf-8"

        data_match = re.search(PAGE_DATA_REGEX, r.text)
        if not data_match:
            raise Exception("Invalid Request response")

        data_str = data_match.group(1).encode("latin1").decode("unicode_escape")
        data = json.loads(data_str)

        descriptions = self.get_descriptions(data)
        if self._district.lower() not in descriptions:
            raise Exception(
                f"District {self._district} not found, use one of {list(descriptions.keys())}"
            )

        entries = []
        description = descriptions[self._district.lower()]
        for collection in description.split("\n"):
            bin_type, days = collection.split("=>")
            days = days.split("|")[0].strip()
            for day in days.split(","):
                collection_day = FRENSH_WEEKDAYS[day.strip().lower()]
                for dt in rrule(
                    freq=WEEKLY,
                    dtstart=date.today(),
                    count=20,
                    byweekday=collection_day,
                ):
                    entries.append(
                        Collection(
                            date=dt.date(),
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type.split()[-1]),
                        )
                    )

        return entries
