import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup, Tag
from dateutil.rrule import FR, MO, MONTHLY, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Malta"
DESCRIPTION = "Nation wide collection schedule for Malta"
URL = "https://www.wastecollection.mt/"

TEST_CASES: dict[str, dict] = {"test": {}}


ICON_MAP = {
    "Mixed": "mdi:trash-can",
    "Recycled": "mdi:recycle",
    "Organic": "mdi:leaf",
    "glass": "mdi:bottle-soda",
}


API_URL = "https://www.wastecollection.mt/"

DAYS = {
    "monday": MO,
    "tuesday": TU,
    "wednesday": WE,
    "thursday": TH,
    "friday": FR,
    "saturday": SA,
    "sunday": SU,
}

TIMING_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "last": -1}


class Source:
    def __init__(self):
        pass

    @staticmethod
    def _parse_normal(tag: Tag) -> tuple[str | None, rrule | None]:
        dtstart = datetime.now()
        dtstop = datetime.now() + timedelta(days=365)
        strong = tag.select_one("strong")
        if not strong:
            return None, None

        weekday_str = strong.text.strip()
        weekday = DAYS.get(weekday_str.strip(":").lower())
        if not weekday:
            return None, None

        bin_type_str = tag.text.split(":")[1].strip()

        return bin_type_str, rrule(
            WEEKLY, byweekday=weekday, dtstart=dtstart, until=dtstop
        )

    @staticmethod
    def _parse_flowtext(tag: Tag) -> tuple[str | None, rrule | None]:
        dtstart = datetime.now()
        dtstop = datetime.now() + timedelta(days=365)

        text = tag.text.strip()
        if not text.lower().startswith("the collection") or text.lower().startswith(
            "the collection times timetable"
        ):
            return None, None

        words = text.split()

        type_start = False
        shedule_start = False
        bin_type_str = ""
        weekday = None
        timings = []
        for word in words:
            word = word.strip()
            if word == "of" and not shedule_start:
                type_start = True
                continue
            if word == "will":
                type_start = False
                shedule_start = True
                continue
            if type_start:
                bin_type_str += word + " "
                continue
            if word in TIMING_WORDS:
                timings.append(TIMING_WORDS[word])
                continue
            if word.lower() in DAYS:
                weekday = DAYS[word.lower()]
                continue

        bin_type_str = bin_type_str.strip()

        if weekday and timings and bin_type_str:
            # RRULE Every timing'th weekday of the month
            return bin_type_str, rrule(
                MONTHLY,
                byweekday=weekday,
                bysetpos=timings,
                dtstart=dtstart,
                until=dtstop,
            )

        _LOGGER.warning("Failed to parse flowtext,", text)
        return None, None

    def fetch(self) -> list[Collection]:
        rules: dict[str, list[rrule]] = {}
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        for p in soup.select("p"):
            if p.find("strong"):
                bin_type, rule = self._parse_normal(p)
            else:
                bin_type, rule = self._parse_flowtext(p)

            if bin_type and rule:
                rules[bin_type] = rules.get(bin_type, []) + [rule]
            continue

        entries = []
        for bin_type, rule_list in rules.items():
            bin_type = bin_type.replace(" only", "")
            for rule in rule_list:
                for dt in rule:
                    entries.append(
                        Collection(
                            date=dt.date(),
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type.split()[0]),
                        )
                    )
        return entries
