import logging
import re
import time
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Currently, Montreal does not offer an iCal/Webcal subscription method.
# The GeoJSON file provides sector-specific details.
# The waste collection schedule is then interpreted from English natural language. Not every sector follows the same structure.
# This method is not highly reliable but serves as an acceptable workaround until a better solution is provided by the city.

TITLE = "Montreal (QC)"
DESCRIPTION = "Source script for montreal.ca/info-collectes"
URL = "https://montreal.ca/info-collectes"
TEST_CASES = {
    "Lasalle": {"sector": "LSL4"},
    "Mercier-Hochelaga": {"sector": "MHM_42-5_B"},
    "Ahuntsic": {"sector": "AC-2"},
    "Rosemont": {
        "sector": "RPP-RE-22-OM",
        "recycling": "RPP_MR-5",
        "food": "RPP-RE-22-RA",
        "green": "RPP-RE-22-RV",
        "bulky": "RPP-REGIE-22",
    }
}

API_URL = [
    {
        "type": "Waste",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson",
    },
    {
        "type": "Recycling",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/d02dac7d-a114-4113-8e52-266001447591/download/collecte-des-matieres-recyclables.geojson",
    },
    {
        "type": "Food",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/61e8c7e6-9bf1-45d9-8ebe-d7c0d50cfdbb/download/collecte-des-residus-alimentaires.geojson",
    },
    {
        "type": "Green",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/d0882022-c74d-4fe2-813d-1aa37f6427c9/download/collecte-des-residus-verts-incluant-feuilles-mortes.geojson",
    },
    {
        "type": "Bulky",
        "url": "https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/2345d55a-5325-488c-b4fc-a885fae458e2/download/collecte-des-residus-de-construction-de-renovation-et-de-demolition-crd-et-encombrants.geojson",
    },
]

ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food-apple",
    "Green": "mdi:leaf",
    "Bulky": "mdi:sofa",
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

LOGGER = logging.getLogger(__name__)
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Download on your computer a <a href="https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson">Montreal GeoJSON file</a><br/>Visit https://geojson.io/<br/>Click on *Open* and select the Montreal GeoJSON file<br/>Find your sector on the map.',
    "fr": 'Téléchargez un <a href="https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/5f3fb372-64e8-45f2-a406-f1614930305c/download/collecte-des-ordures-menageres.geojson">fichier Montreal GeoJSON</a><br/>Visitez https://geojson.io/<br/>Ouvrez le fichier Montreal GeoJSON<br/>Trouvez votre secteur sur la carte.'
}

PARAM_TRANSLATIONS = {
    "en": {
        "sector": "Waste sector",
        "recycling": "Recycling sector",
        "bulky": "Bulky items sector",
        "food": "Food waste sector",
        "green": "Greens and leafs sector"
    },
    "fr": {
        "sector": "Secteur ordure ménagère",
        "recycling": "Secteur recyclage",
        "bulky": "Secteur item encombrants",
        "food": "Secteur compost",
        "green": "Secteur résiduts verts et feuilles mortes"
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "sector": "This is the default sector.",
        "recycling": "If value is different from waste sector.",
        "bulky": "If value is different from waste sector.",
        "food": "If value is different from waste sector.",
        "green": "If value is different from waste sector."
    },
    "fr": {
        "sector": "Ce secteur est utilisé par défault",
        "recycling": "Si différent du secteur des ordures ménagères.",
        "bulky": "Si différent du secteur des ordures ménagères.",
        "food": "Si différent du secteur des ordures ménagères.",
        "green": "Si différent du secteur des ordures ménagères."
    }
}

class Source:
    def __init__(self, sector: str, recycling: str = None, bulky: str = None, food: str = None, green: str = None):
        self._sector: dict = {
            'waste': sector,
            'recycling': recycling if recycling else sector,
            'bulky': bulky if bulky else sector,
            'food': food if food else sector,
            'green': green if green else sector
        }

    def parse_collection(self, source_type, schedule_message):
        """
        Parse GeoJSON from Info-Collecte data
        """
        entries = []
        # Searching for the weekday in the sentence
        collection_day = None
        for day in WEEKDAYS.keys():
            if re.search(day, schedule_message, re.IGNORECASE):
                collection_day = WEEKDAYS[day]
                break  # Stop searching if the day is found

        # These happens weekly
        if source_type in ['Waste', 'Food', 'Recycling', 'Bulky']:
            # Iterate through each month and day, and handle the "out of range" error
            for month in range(1, 13):
                for day in range(1, 32):
                    try:
                        date = datetime(datetime.now().year, month, day)
                        if date.weekday() != collection_day:  # Tuesday has index 1
                            continue
                        entries.append(
                            Collection(
                                date=date.date(),
                                t=source_type,
                                icon=ICON_MAP.get(source_type),
                            )
                        )
                    except ValueError:
                        pass  # Skip if the day is out of range for the month
            return entries

        days = []
        season = schedule_message.split('-')
        header = season.pop(0)
        # Extract year
        if re.match(r'.*(20\d\d).*', header):
            year = int(re.match(r'.*(20\d\d).*', header).group(1))
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
            # There could be seasonal schedules, every week, every other week or speicific dates
            if re.match(r'.*[fF]rom (.*) to (.*)', line):
                date_range = re.match(r'.*[fF]rom (.*) to (.*)', line)
                date_range_start = date_range.group(1)
                date_range_stop = date_range.group(2)
                for month, month_id in MONTHS.items():
                    if re.search(rf'{month}', date_range_start, re.IGNORECASE):
                        month_start = month_id
                    if re.search(rf'{month}', date_range_stop, re.IGNORECASE):
                        month_stop = month_id
                if re.search(r'\d+', date_range_start):
                    day_start = int(re.match(r'.*(\d+).*', date_range_start).group(1))
                if re.search(r'\d+', date_range_stop):
                    day_stop = int(re.search(r'\d+(?!.*\d+)', date_range_stop).group(0))
                within_dates = False
            elif re.match(r'(.*\d+.*){1,}', line):
                # Multiple dates ?
                dates_defined = True
                for month, month_id in MONTHS.items():
                    if re.search(rf'{month}', line, re.IGNORECASE):
                        months_found.append(month)

            for month, month_id in MONTHS.items():
                if date_range and (month_id < month_start or month_id > month_stop):
                    continue
                if dates_defined and month not in months_found:
                    continue
                if re.search("(every )?week(ly)?", line):
                    for day in range(1, 32):
                        try:
                            if not within_dates and day_start == day and month_start == month_id:
                                within_dates = True
                            if within_dates and day_stop >= day and month_stop == month_id:
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

                try:
                    days_in_month = re.search(
                        rf'\b{month}(.*){MONTH_PATTERN}', line, re.IGNORECASE
                    ).group(0)

                    days_in_month = re.split(r", | and ", days_in_month)
                    days_in_month = [part.lstrip().split(" ")[0] for part in days_in_month]

                    # Converting the extracted strings to integers
                    days_numbers = [int(num) for num in days_in_month if num.isnumeric()]

                    for day in days_numbers:
                        date = datetime(year, MONTHS[month], day)
                        days.append(date.date())
                    # break
                except Exception as e:
                    LOGGER.debug('No dates found in string.')
                    break

        entries = []
        for d in days:
            entries.append(
                Collection(
                    date=d,
                    t=source_type,
                    icon=ICON_MAP.get(source_type),
                )
            )
        return entries

    def get_data_by_source(self, source_type, url):
        # Get waste collection zone by longitude and latitude

        r = requests.get(
            url,
            timeout=60
        )
        r.raise_for_status()

        schedule = r.json()
        entries = []

        # check the information for the sector
        for feature in schedule["features"]:
            if feature["properties"]["SECTEUR"] != self._sector[source_type.lower()]:
                continue
            if feature["properties"]["JOUR"] and feature["properties"]["FREQUENCE"]:
                # Not implemented yet
                pass
            else:
                schedule_message = feature["properties"]["MESSAGE_EN"]
                entries += self.parse_collection(source_type, schedule_message)

        return entries

    def fetch(self):
        entries = []
        for source in API_URL:
            try:
                if self._sector[source["type"].lower()] is not None:
                    entries += self.get_data_by_source(source["type"], source["url"])
                else:
                    LOGGER.warning(
                        f"Skipped {source['type']} schedule as no sector was provided."
                    )
            except Exception as e:
                # Probably because the natural language format does not match known formats.
                LOGGER.error("Error", exc_info=True)
                LOGGER.warning(
                    f"Error while parsing {source['type']} schedule. Ignored."
                )
        return entries
