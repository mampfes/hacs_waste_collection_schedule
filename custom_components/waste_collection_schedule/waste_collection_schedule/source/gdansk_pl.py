import datetime

import requests

from ..collection import Collection  # type: ignore[attr-defined]
from ..exceptions import SourceArgumentNotFound, SourceArgAmbiguousWithSuggestions, SourceArgumentNotFoundWithSuggestions

TITLE = "Gdańsk"
DESCRIPTION = "Source for city of Gdańsk garbage collection"
URL = "https://czystemiasto.gdansk.pl/harmonogram-odbioru-odpadow/"
TEST_CASES = {
    "Oliwa": {
        "street_name": "Alfa Liczmańskiego",
        "street_number": "11",
        "housing_type": "Firmy",
    },
    "Incomplete": {
        "street_name": "Liczmańskiego",
        "street_number": "11",
        "housing_type": "Zabudowa wielorodzinna",
    },
    "Olszynka": {
        "street_name": "Osiedle",
        "street_number": "2",
        "housing_type": "Zabudowa jednorodzinna",
    },
    "Niedźwiednik": {
        "street_name": "Leśna Góra",
        "street_number": "1B",
        "housing_type": "Zabudowa jednorodzinna",
    },
    "Aleja Grunwaldzka": {
        "street_name": "Aleja Grunwaldzka",
        "street_number": "137",
        "housing_type": "Zabudowa jednorodzinna",
    },
}

API_URL = "https://pluginecoapi.ecoharmonogram.pl/v1/"
ICON_MAP = {
    "RESZTKOWE": "mdi:trash-can",
    "PAPIER": "mdi:file-outline",
    "METALE I TWORZYWA SZTUCZNE": "mdi:recycle",
    "SZKŁO": "mdi:glass-fragile",
    "BIO": "mdi:leaf",
    "WIELKOGABARYTY": "mdi:dump-truck",
    "ODPADY ZIELONE*": "mdi:tree",
    "TERMINY PŁATNOŚCI": "mdi:currency-usd",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Please make sure the street name is exactly as in the official Czyste Miasto Gdańsk app. Eg. "Aleja Grunwaldzka", not just "Grunwaldzka" for best results',
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_name": "Street",
        "street_number": "Number",
        "housing_type": 'Type of housing, choose from "Zabudowa jednorodzinna", "Zabudowa wielorodzinna" or "Firmy"',
    },
}

COMMUNITY = 108 # Seems hardcoded
SCHEDULE_PERIODS = "schedulePeriodsWithDataForCommunity"
TOWNS = "townsForCommunity"
STREETS_FOR_TOWN = "streetsForTown"
STREETS = "streets"
SCHEDULES = "schedules"

SINGLE_FAMILIY = "Zabudowa jednorodzinna"
MULTIPLE_FAMILY = "Zabudowa wielorodzinna"


class Source:
    def __init__(self, street_name: str, street_number: str | int, housing_type: str = "Zabudowa wielorodzinna"):
        self._street_name = street_name
        self._street_number = str(street_number).upper()
        self._housing_type = housing_type

    def _get_schedule_period_id(self):
        data = {
            "communityId": COMMUNITY,
        }
        r = requests.post(f"{API_URL}{SCHEDULE_PERIODS}", data=data)
        r.raise_for_status()
        res = r.json()
        return res['data']['schedulePeriods'][0]['id']

    def _get_town_id(self):
        data = {
            "communityId": COMMUNITY,
        }
        r = requests.post(f"{API_URL}{TOWNS}", data=data)
        r.raise_for_status()
        res = r.json()
        return res['data']['towns'][0]['id']

    def _get_street_cluster_id(self, schedule_period_id: str, town_id: str):
        data = {
            "schedulePeriodId": schedule_period_id,
            "townId": town_id,
        }
        r = requests.post(f"{API_URL}{STREETS_FOR_TOWN}", data=data)
        r.raise_for_status()
        res = r.json()
        matches = []
        for street in res['data']:
            if self._street_name.upper() in street['name'].upper():
                matches.append(street)

        if len(matches) == 1:
            self._street_name = matches[0]['name']  # Fix casing
            return matches[0]['choosedStreetIds']  # sic! xD
        elif len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions("street_name", self._street_name, [s['name'] for s in matches])
        else:
            raise SourceArgumentNotFound("street_name", self._street_name)

    def _get_street_id(self, schedule_period_id: str,  town_id: str, street_cluster_id: str):
        data = {
            "schedulePeriodId": schedule_period_id,
            "townId": town_id,
            "choosedStreetIds": street_cluster_id,
            "number": self._street_number,
            "groupId": "1",
        }
        r = requests.post(f"{API_URL}{STREETS}", data=data)
        r.raise_for_status()
        res = r.json()

        options = []
        matches = []
        for group in res['data']['groups']['items']:
            options.append(group['name'])
            if self._housing_type.upper() in group['name'].upper():
                matches.append(group)

        if len(matches) == 1:
            self._housing_type = matches[0]['name']
            return matches[0]['choosedStreetIds'].split(',')[0]  # Weird, but orignal app seems to take first
        elif len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions("housing_type", self._housing_type, [s['name'] for s in matches])
        else:
            raise SourceArgumentNotFoundWithSuggestions("housing_type", self._housing_type, options)

    def _get_schedule(self, schedule_period_id: str, town_id: str, street_id: str):
        data = {
            "schedulePeriodId": schedule_period_id,
            "townId": town_id,
            "streetId": street_id,
            "number": self._street_number,
            "streetName": self._street_name,
        }
        r = requests.post(f"{API_URL}{SCHEDULES}", data=data)
        r.raise_for_status()
        res = r.json()

        # We return the mapping of collection types and list of dates to be processed later
        mapping = {}
        for desc in res['data']['scheduleDescription']:
            mapping[desc['id']] = {
                'name': desc['name'],
                'icon': ICON_MAP.get(desc['name'], "mdi:recycle"),
            }

        return mapping, res['data']['schedules']

    def fetch(self) -> list[Collection]:
        schedule_period_id = self._get_schedule_period_id()
        town_id = self._get_town_id()
        street_cluster_id = self._get_street_cluster_id(schedule_period_id, town_id)
        street_id = self._get_street_id(schedule_period_id, town_id, street_cluster_id)
        mapping, schedule = self._get_schedule(schedule_period_id, town_id, street_id)

        entries = []
        for item in schedule:
            mapping_item = mapping[item['scheduleDescriptionId']]
            for day in item['days'].split(';'):
                entries.append(
                    Collection(
                        datetime.date(int(item['year']), int(item['month']), int(day)),
                        mapping_item['name'],
                        mapping_item['icon'],
                    )
                )

        return entries
