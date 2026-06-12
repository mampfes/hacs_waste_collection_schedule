import logging
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Repentigny (QC)"
DESCRIPTION = "Source script for Ville de Repentigny waste collection using Quebec open data portal"
URL = "https://www.donneesquebec.ca/recherche/dataset/8a36b825-def9-4ce8-b7e2-6f8d2f8ce246/resource/8683e519-c133-402c-b173-9807d592c487/download/collectematieresresiduelles2018.json"

TEST_CASES = {
    "Sector A": {"sector": "A"},
    "Sector B": {"sector": "B"},
    "Sector C": {"sector": "C"},
    "Sector D": {"sector": "D"},
}

ICON_MAP = {
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Matières organiques": Icons.ORGANIC,
    "Matières recyclables": Icons.RECYCLING,
}

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
    "Lundi": 0,
    "Mardi": 1,
    "Mercredi": 2,
    "Jeudi": 3,
    "Vendredi": 4,
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

PARAM_TRANSLATIONS = {
    "en": {
        "sector": "Sector",
    },
    "fr": {
        "sector": "Secteur",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "sector": "Your waste collection sector (A, B, C, D, E, or F)",
    },
    "fr": {
        "sector": "Votre secteur de collecte des déchets (A, B, C, D, E ou F)",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Enter your sector manually if you know it from the <a href="https://repentigny.ca/services/citoyens/collectes">collection calendar</a>.',
    "fr": 'Entrez votre secteur manuellement si vous le connaissez d\'après le <a href="https://repentigny.ca/services/citoyens/collectes">calendrier de collecte</a>.',
}

COUNTRY = "ca"


class Source:
    def __init__(self, sector: str | None = None):
        self._sector = sector

        # Validate that sector is provided
        if not sector:
            raise SourceArgumentNotFound(
                "sector", "", "please provide a sector (A, B, C, D, E, or F)"
            )

        # Validate sector is one of the allowed values
        if sector not in ["A", "B", "C", "D", "E", "F"]:
            raise SourceArgumentNotFound(
                "sector", sector, "please provide a valid sector (A, B, C, D, E, or F)"
            )

    def fetch(self):
        """Fetch waste collection schedule for the specified sector."""
        # Fetch the collection data from the Quebec open data portal
        response = requests.get(URL, timeout=30)
        response.raise_for_status()

        data = response.json()
        entries = []

        # Filter data for the specified sector
        sector_data = [item for item in data if item["Secteur"] == self._sector]

        for item in sector_data:
            # Parse the day of the week
            jour = item["Jour"]
            day_of_week = WEEKDAYS.get(jour)
            if day_of_week is None:
                LOGGER.warning(f"Unknown day of week: {jour}")
                continue

            # Parse the frequency
            frequence = item.get("Frequence", "")
            if not frequence:
                LOGGER.warning(f"No frequency specified for {item['TypeDechet']}")
                continue

            # Get the current year
            year = datetime.now().year

            # Find the next occurrence of this day of the week
            # Start from January 1st of the current year
            start_date = datetime(year, 1, 1)
            day_offset = (day_of_week - start_date.weekday()) % 7
            collection_date = start_date + timedelta(days=day_offset)

            # If the collection date is before today, add 7 days (next week)
            if collection_date.date() < datetime.now().date():
                collection_date += timedelta(days=7)

            # Generate multiple dates based on frequency
            collection_type = item["TypeDechet"]
            icon = ICON_MAP.get(collection_type, Icons.GENERAL_WASTE)

            if "semaine" in frequence.lower():
                # Weekly or bi-weekly collections
                if "deux" in frequence.lower():
                    # Bi-weekly (every 2 weeks)
                    max_occurrences = (
                        26  # Approximately 26 bi-weekly collections per year
                    )
                    interval = 14  # 14 days
                else:
                    # Weekly (every 1 week)
                    max_occurrences = 52  # Approximately 52 weekly collections per year
                    interval = 7  # 7 days

                # Generate collection dates
                for i in range(max_occurrences):
                    collection_date = start_date + timedelta(
                        days=day_offset + i * interval
                    )
                    if collection_date.year != year:
                        break
                    if collection_date.date() < datetime.now().date():
                        continue
                    entries.append(
                        Collection(
                            date=collection_date.date(),
                            t=collection_type,
                            icon=icon,
                        )
                    )
            elif "mois" in frequence.lower():
                # Monthly collections
                # Find the day of month (assuming it's the same day as the first occurrence)
                day_of_month = collection_date.day
                max_occurrences = 12  # 12 monthly collections per year
                interval = 30  # Approximate 30 days

                for i in range(max_occurrences):
                    collection_date = datetime(year, 1 + i, day_of_month)
                    if collection_date.date() < datetime.now().date():
                        continue
                    entries.append(
                        Collection(
                            date=collection_date.date(),
                            t=collection_type,
                            icon=icon,
                        )
                    )
            else:
                # Skip irregular/annual collections (no date data available)
                continue

        return entries
