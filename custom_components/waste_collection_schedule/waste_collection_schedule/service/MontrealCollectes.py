"""Montreal "info-collectes" waste schedules (CA).

Montreal publishes no calendar feed. Its open-data GeoJSON files, one per
collection type, carry for every sector a free-text English message ("Collections
take place on TUESDAYS from April 1 to November 30 ..."), and the schedule is read
out of that prose. Not every sector words it the same way, so this is a best
effort until the city publishes dated data.

The five files are fetched in this order (``TARGETS``): Green before Food, because
some sectors word their Food collection as "included in the collection of organic
waste", without a weekday of their own, and then follow the Green schedule.
"""

import logging
import re
from datetime import datetime
from typing import Any

from waste_collection_schedule.parsers import Parser

LOGGER = logging.getLogger(__name__)

_DATASET = (
    "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource"
)

URLS = {
    "Waste": f"{_DATASET}/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson",
    "Recycling": f"{_DATASET}/d02dac7d-a114-4113-8e52-266001447591/download/collecte-des-matieres-recyclables.geojson",
    "Green": f"{_DATASET}/d0882022-c74d-4fe2-813d-1aa37f6427c9/download/collecte-des-residus-verts-incluant-feuilles-mortes.geojson",
    "Food": f"{_DATASET}/61e8c7e6-9bf1-45d9-8ebe-d7c0d50cfdbb/download/collecte-des-residus-alimentaires.geojson",
    "Bulky": f"{_DATASET}/2345d55a-5325-488c-b4fc-a885fae458e2/download/collecte-des-residus-de-construction-de-renovation-et-de-demolition-crd-et-encombrants.geojson",
}
TARGETS = list(URLS.values())

# The source parameter holding each type's sector; an unset one follows ``sector``.
SECTOR_FIELDS = {
    "Waste": "sector",
    "Recycling": "recycling",
    "Green": "green",
    "Food": "food",
    "Bulky": "bulky",
}

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Tuesay": 1,  # Typo in message "Collections take place on TUESAYS" (instead of TUESDAYS).
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

MONTH_PATTERN = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b"

# Some sectors report their Food (organic) waste collection with a message
# such as "Food waste collections is included in the collection of organic
# waste." and no weekday of their own. In that case, Food follows the same
# schedule as the Green (organic waste) collection for the same sector.
FOOD_INCLUDED_IN_GREEN_PATTERN = re.compile(
    r"included in the collection of organic waste", re.IGNORECASE
)

# Biweekly seasons are written as "every two weeks", "every second week" or
# "once every two weeks". The substring "week" also matches the weekly branch
# below, so these lines have to be recognised and excluded from it explicitly.
BIWEEKLY_PATTERN = re.compile(r"every\s+(?:two|second|other|2)\s+weeks?", re.IGNORECASE)

# A sector that enumerates collection days across several months has
# published a schedule, not prose that happens to mention a date. Such a
# message must not take the whole-year weekday expansion, which would
# invent a collection on every remaining weekday of the year.
#
# Counted over the hyphen-delimited body only, because that is what the
# date parser actually reads. A message whose dates sit ahead of the first
# hyphen would otherwise be handed to a parser that cannot see them, and
# would yield nothing at all.
EXPLICIT_DATE_LIST_MIN_MONTHS = 4
MONTH_WITH_DAY_PATTERN = re.compile(
    rf"\b({'|'.join(MONTHS)})\s+\d{{1,2}}\b", re.IGNORECASE
)


def enumerates_dates_across_months(schedule_message):
    """Whether the parsed body lists days in several distinct months."""
    months = {
        match.group(1).lower()
        for line in schedule_message.split("-")[1:]
        for match in MONTH_WITH_DAY_PATTERN.finditer(line)
    }
    return len(months) >= EXPLICIT_DATE_LIST_MIN_MONTHS


def parse_collection(source_type, schedule_message):
    """Dates of one sector's English schedule message, as (date, type) rows."""
    entries = []
    # Searching for the weekday in the sentence
    collection_day = None
    for day in WEEKDAYS:
        if re.search(day, schedule_message, re.IGNORECASE):
            collection_day = WEEKDAYS[day]
            break  # Stop searching if the day is found

    # These happens weekly
    if not re.search(
        r"(?:every\s+(?:.*)week|of the month)", schedule_message, re.IGNORECASE
    ) and not enumerates_dates_across_months(schedule_message):
        # Iterate through each month and day, and handle the "out of range" error
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    date = datetime(datetime.now().year, month, day)
                    if date.weekday() != collection_day:  # Tuesday has index 1
                        continue
                    entries.append((date.date(), source_type))
                except ValueError:
                    pass  # Skip if the day is out of range for the month
        return entries

    days = []
    season = schedule_message.split("-")
    header = season.pop(0)
    # Extract year
    if re.match(r".*(20\d\d).*", header):
        year = int(re.match(r".*(20\d\d).*", header).group(1))
    else:
        year = datetime.now().year
    for line in season:
        date_range = False
        dates_defined = False
        months_found = []
        month_start = 1
        month_stop = 12
        day_start = 1
        day_stop = 31
        within_dates = False
        # There could be seasonal schedules, every week, every other week or specific dates
        if re.match(r".*[fF]rom (.*) to (.*)", line):
            date_range = re.match(r".*[fF]rom (.*) to (.*)", line)
            date_range_start = date_range.group(1)
            date_range_stop = date_range.group(2)
            for month, month_id in MONTHS.items():
                if re.search(rf"{month}", date_range_start, re.IGNORECASE):
                    month_start = month_id
                if re.search(rf"{month}", date_range_stop, re.IGNORECASE):
                    month_stop = month_id
            if re.search(r"\d+", date_range_start):
                day_start = int(re.search(r"(\d+)", date_range_start).group(1))
            if re.search(r"\d+", date_range_stop):
                day_stop = int(re.search(r"\d+(?!.*\d+)", date_range_stop).group(0))
        elif re.match(r"(.*\d+.*){1,}", line):
            # Multiple dates ?
            dates_defined = True
            for month in MONTHS:
                if re.search(rf"{month}", line, re.IGNORECASE):
                    months_found.append(month)

        for month, month_id in MONTHS.items():
            if date_range and (month_id < month_start or month_id > month_stop):
                continue
            if dates_defined and month not in months_found:
                continue
            if re.search("(every )?week(ly)?", line) and not BIWEEKLY_PATTERN.search(
                line
            ):
                for day in range(1, 32):
                    try:
                        if (
                            not within_dates
                            and day_start == day
                            and month_start == month_id
                        ):
                            within_dates = True
                        if within_dates and day > day_stop and month_stop == month_id:
                            within_dates = False
                        if within_dates:
                            date = datetime(year, month_id, day)
                            if date.weekday() == collection_day:  # Tuesday has index 1
                                days.append(date.date())
                    except ValueError:
                        pass  # Skip if the day is out of range for the month
                continue

            # Splitting the string by ',' and 'and' to extract individual numbers
            line = line.replace(";", "")
            line = line.replace(".", "")
            line = line.replace(":", "")
            line = line.replace("*", "")

            try:
                # Capture only up to the next month name (non-greedy),
                # otherwise a month inherits the day numbers of every
                # later month on the same line. An explicit year right
                # after the month name is skipped so it is not mistaken
                # for a day number.
                days_in_month_match = re.search(
                    rf"\b{month}\b(?:\s+{year})?(.*?)(?={MONTH_PATTERN}|$)",
                    line,
                    re.IGNORECASE | re.MULTILINE,
                )
                if not days_in_month_match:
                    continue
                days_in_month = days_in_month_match.group(1)

                # Treat an Oxford comma as one separator. Splitting on
                # ", " first leaves "and 29" as a token in "1, 15, and
                # 29", and the day is then dropped as non-numeric.
                days_in_month = re.split(r",\s*and\s+|,\s*|\s+and\s+", days_in_month)
                # A day list is a contiguous run of bare numbers.
                # A token that carries words after its number is the
                # end of the list: on sectors that continue in prose
                # on the same line, reading on takes the clock times
                # in "between 7 p.m. and 7 a.m." for days of the
                # month. Leading non-numeric tokens are skipped
                # rather than ending the list, because it can open
                # with an ordinal ("July 1st, 15, and 29") that is
                # not parsed as a day but must not discard the rest.
                days_numbers = []
                for part in days_in_month:
                    token = part.strip()
                    day_match = re.match(r"(\d{1,2})\b", token)
                    if not day_match:
                        if days_numbers:
                            break
                        continue
                    days_numbers.append(int(day_match.group(1)))
                    if token != day_match.group(1):
                        break

                for day in days_numbers:
                    date = datetime(year, MONTHS[month], day)
                    days.append(date.date())
                # break
            except Exception:
                LOGGER.debug("No dates found in string.")
                break

    entries = []
    for d in days:
        entries.append((d, source_type))
    return entries


def _message(features: list, sector: str) -> str | None:
    """The first English message of a sector's features."""
    for feature in features:
        if (
            feature["properties"]["SECTEUR"] == sector
            and feature["properties"]["MESSAGE_EN"]
        ):
            return feature["properties"]["MESSAGE_EN"]
    return None


def schedule_rows(
    source_type: str,
    features: list,
    sector: str,
    green_features: list | None,
) -> list[tuple[Any, str]]:
    """The rows of one type's sector, from that type's GeoJSON features."""
    entries: list = []
    for feature in features:
        properties = feature["properties"]
        if properties["SECTEUR"] != sector:
            continue
        if properties["JOUR"] and properties["FREQUENCE"]:
            # Not implemented yet
            continue
        message = properties["MESSAGE_EN"]
        if not message:
            continue
        if source_type == "Food" and FOOD_INCLUDED_IN_GREEN_PATTERN.search(message):
            message = _message(green_features or [], sector)
            if message is None:
                LOGGER.warning(
                    "Food waste for sector %s is included in the organic waste "
                    "collection, but no matching Green sector was found to "
                    "determine the day.",
                    sector,
                )
                continue
        entries += parse_collection(source_type, message)
    return entries


class MontrealCollectesParser(Parser["list[tuple[Any, str]]"]):
    """Read the five GeoJSON responses (in ``URLS`` order) into ``(date, type)`` rows.

    A type that fails to parse is logged and skipped, as the sector's wording may
    not match any known form.
    """

    def __call__(self, response, source=None) -> "list[tuple[Any, str]]":
        responses = list(response)
        params = source.params if source is not None else {}
        features = {
            source_type: reply.json()["features"]
            for source_type, reply in zip(URLS, responses, strict=True)
        }
        rows: list[tuple[Any, str]] = []
        for source_type, field in SECTOR_FIELDS.items():
            sector = params.get(field) or params["sector"]
            try:
                rows += schedule_rows(
                    source_type, features[source_type], sector, features["Green"]
                )
            except Exception:
                LOGGER.error("Error", exc_info=True)
                LOGGER.warning("Error while parsing %s schedule. Ignored.", source_type)
        return rows
