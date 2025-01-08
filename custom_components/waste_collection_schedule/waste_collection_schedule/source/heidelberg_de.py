import datetime
from datetime import datetime as dt

import requests
from dateutil import parser as date_parser
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule, rruleset
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Heidelberg"
DESCRIPTION = "Support for the waste collection schedule provided by the Office of Waste Management and Municipal Cleansing Heidelberg"
URL = "https://www.heidelberg.de/abfall"

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "collect_residual_waste_weekly": "Weekly residual waste collection",
        "even_house_number": "House number to collect from is even",
    },
    "de": {
        "street": "Straße",
        "collect_residual_waste_weekly": "Wöchentliche Abholung des Restmülls",
        "even_house_number": "Hausnummer der Abholadresse ist gerade",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "The street you want to get the waste collection schedule for.",
    },
    "de": {
        "street": "Die Straße, für die ein Abfallkalender angelegt werden soll.",
    },
}

TEST_CASES = {
    "Typical street": {"street": "Alte Bergheimer Straße"},
    "No weekly collection of residual and bio waste possible": {
        "street": "Molkenkurweg"
    },
    "Bi-weekly residual collection as option - uneven street number": {
        "street": "Alte Bergheimer Straße",
        "collect_residual_waste_weekly": False,
        "even_house_number": False,
    },
    "Bi-weekly residual collection as option - even street number": {
        "street": "Alte Bergheimer Straße",
        "collect_residual_waste_weekly": False,
        "even_house_number": True,
    },
}

WASTE_TYPES = {
    "bio": "bio",
    "dsd": "dsd",
    "paper": "paper",
    "rest": "rest",
    "christmas": "christmas",
}

WASTE_MAP = {
    "bio": "Biomüll",
    "dsd": "Gelbe Tonne",
    "paper": "Papiermüll",
    "rest": "Restmüll",
    "christmas": "Weihnachtsbaum",
}

SCHEDULE_TYPES = {
    "all_weeks": "A",
    "uneven_weeks": "U",
    "even_weeks": "G",
}

ICON_MAP = {
    "bio": "mdi:bio",
    "dsd": "mdi:recycle",
    "paper": "mdi:package-variant",
    "rest": "mdi:trash-can",
    "christmas": "mdi:pine-tree",
}

WEEKDAY_MAP = {
    "Mo": MO,
    "Di": TU,
    "Mi": WE,
    "Do": TH,
    "Fr": FR,
    "Sa": SA,
    "So": SU,
}

STREETNAMES_API_URL = "https://garbage.datenplattform.heidelberg.de/streetnames"
COLLECTIONS_API_URL = (
    "https://garbage.datenplattform.heidelberg.de/collections?street={street}"
)


class PostponementInformation:
    def __init__(self, original_date, new_date):
        self.original_date = original_date
        self.new_date = new_date


class WasteInformation:
    def __init__(
        self,
        name: str,
        collection_schedule: int | None,
        collection_weekday: str | None,
        ruleset: rruleset,
    ):
        self.name = name
        self.icon = ICON_MAP[name]
        self._collection_schedule = collection_schedule if collection_schedule else None
        self._collection_weekday = (
            WEEKDAY_MAP[collection_weekday] if collection_weekday else None
        )
        self._collection_ruleset = ruleset

    def _generate_weekdays(self):
        today = dt.today()
        last_week = today - datetime.timedelta(days=7)

        next_year = today.year + 1
        second_week_of_next_year = dt.strptime(f"{next_year}-W2-D7", "%Y-W%W-D%u")

        raw_collection_dates = rrule(
            freq=WEEKLY,
            dtstart=last_week,
            until=second_week_of_next_year,
            byweekday=self._collection_weekday,
            byhour=0,
            byminute=0,
            bysecond=0,
        )

        self._collection_ruleset.rrule(raw_collection_dates)

    def _exclude_weekdays_without_collection(self):
        weekdays_without_collection = []

        if self._collection_schedule == SCHEDULE_TYPES["uneven_weeks"]:
            weekdays_without_collection = list(
                filter(
                    lambda x: int(x.strftime("%W")) % 2 == 1, self._collection_ruleset
                )
            )

        if self._collection_schedule == SCHEDULE_TYPES["even_weeks"]:
            weekdays_without_collection = list(
                filter(
                    lambda x: int(x.strftime("%W")) % 2 == 0, self._collection_ruleset
                )
            )

        for weekday_without_collection in weekdays_without_collection:
            self._collection_ruleset.exdate(weekday_without_collection)

    def _include_relevant_postponements(
        self, postponement_data: list[PostponementInformation]
    ):
        original_collection_dates = list(self._collection_ruleset)

        for postponement in postponement_data:
            if postponement.original_date in original_collection_dates:
                self._collection_ruleset.exdate(postponement.original_date)
                self._collection_ruleset.rdate(postponement.new_date)

    def generate_collection_ruleset(
        self, postponement_data: list[PostponementInformation]
    ):
        if self.name == WASTE_TYPES["christmas"]:
            # Collection date is already generated by extract_collection_data
            # as Christmas trees are collected only once a year
            return

        self._generate_weekdays()
        self._exclude_weekdays_without_collection()
        self._include_relevant_postponements(postponement_data)

    def get_collection_dates(self) -> list[datetime.date]:
        return list(map(lambda x: x.date(), list(self._collection_ruleset)))


class Source:
    def __init__(
        self,
        street: str,
        collect_residual_waste_weekly: bool = True,
        even_house_number: bool = False,
    ):
        self._street = street
        self._api_url = COLLECTIONS_API_URL.format(street=self._street)
        self._collect_residual_waste_weekly = collect_residual_waste_weekly
        self._even_house_number = even_house_number

    @staticmethod
    def get_available_streets() -> list[str]:
        streets_request = requests.get(STREETNAMES_API_URL)
        streets_request.raise_for_status()

        available_streets = []

        for street in streets_request.json():
            available_streets.append(street)

        return available_streets

    def _extract_collection_data(self, raw_collection_data):
        collection_data = []

        for waste_type in WASTE_TYPES:
            if waste_type == WASTE_TYPES["christmas"]:
                collection_date = date_parser.parse(
                    raw_collection_data[waste_type][0]["collection_date"], ignoretz=True
                )
                ruleset = rruleset()
                ruleset.rdate(collection_date)

                collection_data.append(
                    WasteInformation(waste_type, None, None, ruleset)
                )
            else:
                if (
                    waste_type == WASTE_TYPES["rest"]
                    and self._collect_residual_waste_weekly is False
                ):
                    collection_schedule = (
                        SCHEDULE_TYPES["even_weeks"]
                        if self._even_house_number is True
                        else SCHEDULE_TYPES["uneven_weeks"]
                    )
                else:
                    collection_schedule = raw_collection_data["collections"][0][
                        f"calendar_week_{waste_type}"
                    ]

                collection_data.append(
                    WasteInformation(
                        waste_type,
                        collection_schedule,
                        raw_collection_data["collections"][0][
                            f"day_of_week_{waste_type}"
                        ],
                        rruleset(),
                    )
                )

        return collection_data

    @staticmethod
    def _extract_all_postponement_dates(raw_collection_data):
        postponement_data = []

        for exception in raw_collection_data["exceptions"]:
            original_collection_date = date_parser.parse(
                exception["shift_from_date"], ignoretz=True
            )
            new_collection_date = date_parser.parse(
                exception["shift_to_date"], ignoretz=True
            )

            postponement_data.append(
                PostponementInformation(
                    original_collection_date,
                    new_collection_date,
                )
            )

        return postponement_data

    def fetch(self) -> list[Collection]:
        if len(self._street) == 0:
            raise SourceArgumentRequiredWithSuggestions(
                "street",
                "It's required to specify your street.",
                self.get_available_streets(),
            )

        collections_request = requests.get(self._api_url)
        collections_request.raise_for_status()
        raw_collection_data = collections_request.json()

        if len(raw_collection_data["collections"]) == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, self.get_available_streets()
            )

        collection_data = self._extract_collection_data(raw_collection_data)
        postponement_data = self._extract_all_postponement_dates(raw_collection_data)
        entries = []

        for waste_type in collection_data:
            waste_type.generate_collection_ruleset(postponement_data)

            for collection_date in waste_type.get_collection_dates():
                entries.append(
                    Collection(
                        date=collection_date,
                        t=WASTE_MAP[waste_type.name],
                        icon=waste_type.icon,
                    )
                )

        return entries



