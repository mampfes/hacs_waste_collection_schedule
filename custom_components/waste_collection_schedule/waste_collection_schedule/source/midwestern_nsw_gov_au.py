from datetime import date
import calendar
import json

import requests

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Mid-Western Regional Council"
DESCRIPTION = "Source for Mid-Western Regional Council waste collection schedules."
URL = "https://www.midwestern.nsw.gov.au/"
COUNTRY = "au"

API_URL = "https://www.midwestern.nsw.gov.au/ocapi/calendars/getcalendaritems"
LANGUAGE_CODE = "en-AU"
MONTHS_TO_FETCH = 12

TEST_CASES = {
    "Mudgee North Monday": {"area": "mudgee_north_monday"},
    "Mudgee North Thursday": {"area": "mudgee_north_thursday"},
    "Mudgee South Tuesday": {"area": "mudgee_south_tuesday"},
    "Mudgee South Wednesday": {"area": "mudgee_south_wednesday"},
    "Gulgong Monday": {"area": "gulgong_monday"},
    "Gulgong Thursday": {"area": "gulgong_thursday"},
    "Kandos/Rylstone Friday": {"area": "kandos_rylstone_friday"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "area": "Collection area",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "area": "Collection area as listed by Mid-Western Regional Council.",
    }
}

ICON_MAP = {
    "waste": "mdi:trash-can-outline",
    "organic": "mdi:leaf",
    "recycle": "mdi:recycle",
    "paper": "mdi:newspaper",
}

LABEL_MAP = {
    "LANDFILL": "waste",
    "FOOD AND GARDEN": "organic",
    "RECYCLING": "recycle",
    "PAPER AND CARDBOARD": "paper",
}

MONDAY_THURSDAY_IDS = [
    "cf9dcec1-4072-4068-8080-d494837dc275",
    "ec2967b5-b13e-41a9-8f83-2e988f67fc6a",
    "a2c28b3f-5e53-4c7b-8c8a-045dc1e16fb2",
    "ae79f069-472e-4ec1-9a9b-bd7c0bf45ae2",
]

TUESDAY_WEDNESDAY_IDS = [
    "b3a2a212-edb8-44cf-a306-21d4e4c1be81",
    "649f4490-eed3-44e3-a5ab-cf747b0fccc8",
    "cc86a639-87ce-4347-a10c-e5fea9059e24",
    "1ab0e286-d710-436f-8086-c8051fc267f7",
]

FRIDAY_IDS = [
    "938a1031-73fe-4f38-a660-22982cc2678c",
    "5bf0474c-11a8-48de-a052-493335024b33",
    "e8ee40eb-40a7-463c-b761-d46194565780",
    "5284d0b5-9d5a-446c-b2fc-6c0868aabfd3",
]

AREAS = {
    "mudgee_north_monday": {
        "weekday": "Monday",
        "ids": MONDAY_THURSDAY_IDS,
    },
    "mudgee_north_thursday": {
        "weekday": "Thursday",
        "ids": MONDAY_THURSDAY_IDS,
    },
    "mudgee_south_tuesday": {
        "weekday": "Tuesday",
        "ids": TUESDAY_WEDNESDAY_IDS,
    },
    "mudgee_south_wednesday": {
        "weekday": "Wednesday",
        "ids": TUESDAY_WEDNESDAY_IDS,
    },
    "gulgong_monday": {
        "weekday": "Monday",
        "ids": MONDAY_THURSDAY_IDS,
    },
    "gulgong_thursday": {
        "weekday": "Thursday",
        "ids": MONDAY_THURSDAY_IDS,
    },
    "kandos_rylstone_friday": {
        "weekday": "Friday",
        "ids": FRIDAY_IDS,
    },
}


class Source:
    def __init__(self, area):
        if area not in AREAS:
            raise SourceArgumentNotFoundWithSuggestions(
                "area",
                area,
                list(AREAS.keys()),
            )

        self._weekday = AREAS[area]["weekday"]
        self._calendar_ids = AREAS[area]["ids"]

    def fetch(self):
        entries = []
        today = date.today()

        for month_offset in range(MONTHS_TO_FETCH):
            month_start = self._add_months(today.replace(day=1), month_offset)
            month_end = month_start.replace(
                day=calendar.monthrange(month_start.year, month_start.month)[1]
            )

            payload = {
                "LanguageCode": LANGUAGE_CODE,
                "StartDate": month_start.isoformat(),
                "EndDate": month_end.isoformat(),
                "Ids": self._calendar_ids,
            }

            response = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                raise Exception(f"MWRC API error: {data}")

            entries.extend(self._parse_month(data))

        return entries

    def _parse_month(self, data):
        entries = []

        for day in data.get("data", []):
            if day.get("Day") != self._weekday:
                continue

            try:
                collection_date = date(
                    int(day["YYYY"]),
                    int(day["MM"]),
                    int(day["DD"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

            for item in day.get("Items", []):
                label = item.get("Name", "").strip().upper()
                waste_type = LABEL_MAP.get(label)

                if waste_type is None:
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries

    @staticmethod
    def _add_months(start_date, months):
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1

        return date(year, month, 1)