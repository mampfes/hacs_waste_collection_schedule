import calendar
import re
from datetime import datetime, timedelta, timezone

import requests
from dateutil.rrule import DAILY, FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule, rruleset
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Publidata (Canada) generic source"
DESCRIPTION = "Publidata is a Canadian public operator. Check if your area is concerned on their website."
URL = "https://www.publidata.ca"
COUNTRY = "ca"

TEST_CASES = {
    "Sainte-Julie City Hall": {
        "address": "1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2",
    },
    "Calixa-Lavallée City Hall": {
        "address": "771 Chem. de la Beauce, Calixa-Lavallée, QC J0L 1A0"
    },
    "Contrecoeur City Hall": {
        "address": "5000 Rte Marie-Victorin, Contrecoeur, QC J0L 1C0"
    },
    # "Saint-Amable City Hall": {
    #     "address": "575 Rue Principale, Saint-Amable, QC J0L 1N0"
    # },
    # "Varennes City Hall": {
    #     "address": "175 Rue Sainte-Anne, Varennes, QC J3X 1R6"
    # },
    # "Verchères City Hall" : {
    #     "address": "581 QC-132, Verchères, QC J0L 2R0"
    # },
}

ICON_MAP = {
    "omr": "mdi:trash-can",
    "emb": "mdi:recycle",
    "enc": "mdi:truck-remove",
    "dv": "mdi:leaf",
    "bio": "mdi:compost",
    "verre": "mdi:bottle-wine",
    "sapin": "mdi:pine-tree-variant",
}

LABEL_MAP = {
    "omr": "Ordures ménagères",
    "emb": "Recyclage",
    "enc": "Volumineux",
    "dv": "Feuilles",
    "bio": "Compost",
    "verre": "Verres",
    "sapin": "Sapin de Noël",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your full address / Votre adresse complete",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address / Adresse",
    },
}

EXTRA_INFO = [
    {
        "title": "MRC Marguerite-D'Youville",
        "url": "https://margueritedyouville.ca/",
    },
]

_CALENDAR_DAY_VERY_ABBR = {
    "Mo": MO,
    "Tu": TU,
    "We": WE,
    "Th": TH,
    "Fr": FR,
    "Sa": SA,
    "Su": SU,
}

_CALENDAR_MONTHS_ABBR = [m for m in calendar.month_abbr if m]


class Source:
    geocoder_url = "https://api.publidata.ca/v2/geocoder"

    def __init__(self, address):
        self.address = address

    def _get_address_params(self, address):
        params = {
            "q": address,
            "limit": 10,
            "lookup": "publidata",
        }
        response = requests.get(self.geocoder_url, params=params)

        if response.status_code != 200:
            raise SourceArgumentException("address", "Error response from geocoder")

        data = response.json()[0]["data"]["features"]
        if not data:
            raise SourceArgumentException(
                "address", "No results found for the given address"
            )

        lat, lon = data[0]["geometry"]["coordinates"]

        return {
            "lat": lat,
            "lon": lon,
            "address_id": data[0]["properties"]["id"],
        }

    def _perform_query(self):
        api_url = "https://api.publidata.ca/v2/search"

        params = {
            "size": 999,
            "types[]": "Platform::Services::WasteCollection",
            "collection_modes[]": "truck",
            "address_id": self.address_params["address_id"],
        }

        response = requests.get(api_url, params=params)

        if response.status_code != 200:
            raise Exception(
                f"Error fetching data from {api_url}: {response.status_code}"
            )

        return self._sanitize_response(response.json())

    def _sanitize_response(self, data):
        r"""
        Sanitize the response from the publidata API to extract the collection schedules for each type of waste.

        Example output:
        {
            "emb": {
                "schedules": [
                    {
                        "end_at": "2024-09-30T00:00:00.000+00:00",
                        "schedule_type": "closed",
                        "opening_hours": "2024 Jan 01-2024 Sep 30 off \"Fermeture\"",
                        "name": "Horaires de collecte",
                        "id": 1020853,
                        "start_at": "2024-01-01T00:00:00.000+00:00"
                    },
                    {
                        "end_at": "2024-12-29T00:00:00.000+00:00",
                        "schedule_type": "regular",
                        "opening_hours": "week 2-52/2 Mo 12:00-17:00",
                        "name": "Horaires de collecte",
                        "id": 1019827,
                        "start_at": "2024-01-08T00:00:00.000+00:00"
                    }
                ]
            },
            "omr": {
                "schedules": [
                    {
                    "end_at": "2024-09-30T00:00:00.000+00:00",
                    "schedule_type": "closed",
                    "opening_hours": "2024 Jan 01-2024 Sep 30 off \"Fermeture\"",
                    "name": "Horaires de collecte",
                    "id": 1020854,
                    "start_at": "2024-01-01T00:00:00.000+00:00"
                },
                {
                    "end_at": "2024-12-31T00:00:00.000+00:00",
                    "schedule_type": "regular",
                    "opening_hours": "Tu 05:00-12:00",
                    "name": "Horaires de collecte",
                    "id": 1019829,
                    "start_at": "2024-01-01T00:00:00.000+00:00"
                }
            ]
        }
        """
        result = {}
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            raise Exception("Unexpected response format")

        for hit in hits:
            source = hit.get("_source", {})
            if source.get("metas", {}).get("sectorization") == "single":
                garbage_type = source.get("metas", {}).get("garbage_types", [""])[0]
                if garbage_type:
                    result[garbage_type] = {"schedules": source.get("schedules", {})}
        return result

    def _parse_closure(self, schedule):
        """Parse a closure schedule and return a daily rrule between the start and end dates."""
        start_date = datetime.strptime(schedule["start_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
        end_date = datetime.strptime(schedule["end_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
        return rrule(freq=DAILY, dtstart=start_date, until=end_date)

    def _is_week_day(self, input_string):
        return any(day in input_string for day in _CALENDAR_DAY_VERY_ABBR)

    def _parse_week_day(self, input_string):
        """Parse a string like "Mo" "Tu[2]", "We[2,4]" or "We,Th,Fr" and return the corresponding rrule.weekday object."""
        weekdays = []
        matches = re.findall(r"([A-Za-z]{2})(?:\[(\d+(?:,\d+)*)\])?", input_string)
        for day_of_week, nth_str in matches:
            if nth_str:
                nth = [int(n) for n in nth_str.split(",")]
                weekdays.extend([_CALENDAR_DAY_VERY_ABBR[day_of_week](n) for n in nth])
            else:
                weekdays.append(_CALENDAR_DAY_VERY_ABBR[day_of_week])

        if not weekdays:
            raise ValueError(f"Invalid day format: {input_string}")

        return {"byweekday": weekdays}

    def _is_time(self, input_string):
        return re.match(r"^(\d{2}:\d{2})", input_string)

    def _is_day_number(self, input_string):
        return bool(re.match(r"^(\d{1,2})(,\d{1,2})*$", input_string))

    def _parse_day_number(self, input_string):
        return {"bymonthday": [int(day) for day in input_string.split(",")]}

    def _is_month(self, input_string):
        return any(month in input_string for month in _CALENDAR_MONTHS_ABBR)

    def _parse_month(self, input_string):
        print(input_string)
        input_string = input_string.replace(
            ":", ""
        )  # match some actual cases in production
        if "-" in input_string and "," in input_string:
            month_list = list

        if "-" in input_string:
            start_month, end_month = input_string.split("-")
            month_list = list(
                range(
                    _CALENDAR_MONTHS_ABBR.index(start_month) + 1,
                    _CALENDAR_MONTHS_ABBR.index(end_month) + 1,
                )
            )
        else:
            month_list = [
                _CALENDAR_MONTHS_ABBR.index(month) + 1
                for month in input_string.split(",")
            ]

        return {"bymonth": month_list}

    def _is_year(self, input_string):
        return bool(re.match(r"^(\d{4})", input_string))

    def _parse_year(self, input_string):
        if "-" in input_string:
            start_year, end_year = (int(year) for year in input_string.split("-"))
        elif "," in input_string:
            years = [int(year) for year in input_string.split(",")]
            if years != list(range(min(years), max(years) + 1)):
                raise ValueError(f"Invalid year range: {input_string}")
            start_year = min(years)
            end_year = max(years)
        else:
            start_year = int(input_string)
            end_year = start_year

        return {
            "dtstart": datetime(start_year, 1, 1, tzinfo=timezone.utc),
            "until": datetime(end_year, 12, 31, tzinfo=timezone.utc),
        }

    def _parse_part(self, part):
        """Parse a part of the opening_hours string and return the corresponding kwargs to rrule constructor.

        Example:
            "Sep-Nov" -> {"bymonth": [9, 10, 11]}
            "We[2,4]" -> {"byweekday": WE(2), WE(4)}
            "2024-2025" -> {"dtstart": datetime(2024, 1, 1, tzinfo=timezone.utc), "until": datetime(2025, 12, 31, tzinfo=timezone.utc)}
        """
        if self._is_year(part):
            return self._parse_year(part)
        elif self._is_month(part):
            return self._parse_month(part)
        elif self._is_week_day(part):
            return self._parse_week_day(part)
        elif self._is_day_number(part):
            return self._parse_day_number(part)
        elif self._is_time(part):
            return {}  # ignore those, the plugin doesn’t support time
        else:
            raise ValueError(f"Invalid part: {part}")

    def _parse_week_no(self, input_string):
        week_nos = []
        for sub_string in input_string.split(","):
            if "-" not in sub_string:
                week_nos.append(int(sub_string))
                continue

            weeks = sub_string.split("-")
            start_week = int(weeks[0])
            if "/" in weeks[1]:
                end_week = int(weeks[1].split("/")[0])
                interval = int(weeks[1].split("/")[1])
            else:
                end_week = int(weeks[1])
                interval = 1

            week_nos.extend(list(range(start_week, end_week + 1, interval)))

        return {"byweekno": week_nos}

    def _has_date_list(self, input_string):
        return bool(
            re.search(r"^(\d{4} \w+ \d{1,2}),(\d{4} \w+ \d{1,2})", input_string)
        )

    def _extract_date_list(self, input_string):
        """Split a string containing a date list such as "2024 Jan 01,2024 May 12".

        Return:
        - the date list
        - the remaining string
        """
        match = re.search(r"^(\d{4} \w+ \d{1,2},\d{4} \w+ \d{1,2})(.*)", input_string)
        if match:
            return match.group(1), match.group(2).strip()
        raise ValueError(f"Invalid date range: {input_string}")

    def _has_date_range(self, input_string):
        return bool(
            re.search(r"^(\d{4} \w+ \d{1,2})-(\d{4} \w+ \d{1,2})", input_string)
        )

    def _extract_date_range(self, input_string):
        """Split a string containing a date range such as "2024 Jan 01-2024 May 12".

        Return:
        - the date range
        - the remaining string
        """
        match = re.search(r"^(\d{4} \w+ \d{1,2}-\d{4} \w+ \d{1,2})(.*)", input_string)
        if match:
            return match.group(1), match.group(2).strip()
        raise ValueError(f"Invalid date range: {input_string}")

    def _parse_date_range(self, input_string):
        """Parse a date range such as "2024 Jan 01-2024 May 12" and return the corresponding kwargs to rrule constructor."""
        start_date = datetime.strptime(
            input_string.split("-")[0], "%Y %b %d"
        ).astimezone(timezone.utc)
        end_date = datetime.strptime(input_string.split("-")[1], "%Y %b %d").astimezone(
            timezone.utc
        )
        return {"dtstart": start_date, "until": end_date}

    def _parse_regular(self, schedule):
        """Parse the 'opening_hours' from the input dictionary and return an rruleset object."""
        opening_hours = schedule["opening_hours"]
        start_at = (
            datetime.strptime(schedule["start_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
            if schedule["start_at"]
            else None
        )
        if schedule["end_at"]:
            end_at = datetime.strptime(schedule["end_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            end_at = datetime.now(timezone.utc) + timedelta(days=365)

        rule_set = rruleset()

        # Time range extraction
        time_range_pattern = r"(\d{2}:\d{2})-(\d{2}:\d{2})"
        time_match = re.search(time_range_pattern, opening_hours)
        time_start, time_end = None, None
        if time_match:
            time_start, time_end = time_match.groups()
            opening_hours = opening_hours.replace(
                f"{time_start}-{time_end}", ""
            ).strip()
            start_hour, start_minute, end_hour, end_minute = self._parse_hours(
                time_start, time_end
            )

        # Week ranges
        week_pattern = r"week (\d+(?:-\d+(?:/\d+)?)?(?:,\d+(?:-\d+(?:/\d+)?)?)*)"
        week_match = re.search(week_pattern, opening_hours)
        weeks = None
        if week_match:
            weeks = week_match.group(1)
            opening_hours = opening_hours.replace(f"week {weeks}", "").strip()

        # Weekdays extraction
        weekday_pattern = r"(Mo|Tu|We|Th|Fr|Sa|Su)"
        weekdays = [
            _CALENDAR_DAY_VERY_ABBR[day]
            for day in re.findall(weekday_pattern, opening_hours)
        ]

        # Construct RRULE
        if weeks:
            week_ranges = re.split(r",", weeks)
            for week_range in week_ranges:
                step = 1
                if "/" in week_range:
                    week_range, step = week_range.split("/")
                    step = int(step)
                if "-" in week_range:
                    start_week, end_week = map(int, week_range.split("-"))
                    for week in range(start_week, end_week + 1, step):
                        rule = rrule(
                            freq=WEEKLY,
                            byweekday=weekdays,
                            byhour=start_hour,
                            byminute=start_minute,
                            byweekno=week,
                            dtstart=start_at,
                            until=end_at,
                        )
                        rule_set.rrule(rule)
                else:
                    week = int(week_range)
                    rule = rrule(
                        freq=WEEKLY,
                        byweekday=weekdays,
                        byhour=start_hour,
                        byminute=start_minute,
                        byweekno=week,
                        dtstart=start_at,
                        until=end_at,
                    )
                    rule_set.rrule(rule)

        return rule_set

    @staticmethod
    def _parse_hours(start_time, end_time):
        """Convert time strings to individual hour and minute values."""
        start_hour, start_minute = map(int, start_time.split(":"))
        end_hour, end_minute = map(int, end_time.split(":"))
        return start_hour, start_minute, end_hour, end_minute

    def fetch(self):
        self.address_params = self._get_address_params(self.address)

        entries = []

        sanitized_response = self._perform_query()

        for waste_type, waste_data in sanitized_response.items():
            my_rruleset = rruleset()
            for schedule in waste_data["schedules"]:
                if schedule["schedule_type"] in ("regular", "exception"):
                    my_rruleset.rrule(self._parse_regular(schedule))
                elif schedule["schedule_type"] in ("closed", "closing_exception"):
                    my_rruleset.exrule(self._parse_closure(schedule))
            for entry in my_rruleset:
                entries.append(
                    Collection(
                        entry.date(),
                        LABEL_MAP.get(waste_type, waste_type),
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
