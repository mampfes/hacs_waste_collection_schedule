import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

_LOGGER = logging.getLogger(__name__)

TITLE = "infeo"
DESCRIPTION = "Source for INFEO waste collection."
URL = "https://www.infeo.at/"
EXTRA_INFO = [
    {
        "title": "Bogenschütz Entsorgung",
        "url": "https://bogenschuetz-entsorgung.de",
        "country": "de",
    },
    {
        "title": "Innsbrucker Kommunalbetriebe",
        "url": "https://ikb.at",
        "country": "at",
    },
    {
        "title": "Stadt Salzburg",
        "url": "https://stadt-salzburg.at",
        "country": "at",
    },
]
TEST_CASES = {
    "Bogeschütz": {"customer": "bogenschütz", "zone": "Dettenhausen"},
    "ikb": {"customer": "ikb", "city": "Innsbruck", "street": "Achselkopfweg", "housenumber": "1"},
    "salzburg": {"customer": "salzburg", "city": "Salzburg", "street": "Adolf-Schemel-Straße", "housenumber": "13"},
}

class Source:
    def __init__(self, customer, zone=None, city=None, street=None, housenumber=None):
        self._customer = customer
        self._zone = zone
        self._city = city
        self._street = street
        self._housenumber = None if housenumber is None else str(housenumber)
        self._ics = ICS()
    
    def fetch(self):
        baseUrl = f"https://services.infeo.at/awm/api/{self._customer}/wastecalendar"
        issueUrl = (
            "https://github.com/mampfes/hacs_waste_collection_schedule/issues/new"
        )

        params = {
            "showUnpublishedCalendars": "false",
        }

        # get the available published calendar years
        url = f"{baseUrl}/calendars"
        response = requests.get(url, params=params)
        response.raise_for_status()

        # data validation
        response = response.json()
        if len(response) <= 0:
            raise Exception(
                f"no calendars found, please file an issue at {issueUrl} and mention @dm82m"
            )

        entries = []

        # loop over each calendar year entry and extract data
        for calendarYear in response:
            calendarYearId = calendarYear["id"]
            calendarYearName = calendarYear["name"]

            params = {
                "calendarId": calendarYearId,
            }

            if self._zone != None:

                # get available zones for calendar year
                url = f"{baseUrl}/zones"
                response = requests.get(url, params=params)
                response.raise_for_status()

                # data validation
                response = response.json()
                if len(response) <= 0:
                    _LOGGER.warning(
                        f"no zones found for calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                zoneId = 0

                # try to find the configured and matching zone
                for zone in response:
                    if self._zone in zone["name"]:
                        zoneId = zone["id"]

                if zoneId == 0:
                    _LOGGER.warning(
                        f"zone '{self._zone}' not found in calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                params = {
                    "calendarId": calendarYearId,
                    "zoneId": zoneId,
                    "outputType": "ical",
                }

                # get ical data for year and zone
                url = f"{baseUrl}/v2/export"
                response = requests.get(url, params=params)
                response.raise_for_status()

                dates = self._ics.convert(response.text)

                for d in dates:
                    entries.append(Collection(d[0], d[1]))
                    
            # we will use city, street and housenumber instead of zone
            else:
                
                # CITY
                # get available cities for calendar year
                url = f"{baseUrl}/cities"
                response = requests.get(url, params=params)
                response.raise_for_status()

                # data validation
                response = response.json()
                if len(response) <= 0:
                    _LOGGER.warning(
                        f"no cities found for calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                cityId = 0

                # try to find the configured and matching city
                for city in response:
                    if self._city in city["name"]:
                        cityId = city["id"]

                if cityId == 0:
                    _LOGGER.warning(
                        f"city '{self._city}' not found in calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                # STREET
                # get available streets for calendar year
                
                params = {
                    "calendarId": calendarYearId,
                    "cityId": cityId,
                }
                
                url = f"{baseUrl}/streets"
                response = requests.get(url, params=params)
                response.raise_for_status()

                # data validation
                response = response.json()
                if len(response) <= 0:
                    _LOGGER.warning(
                        f"no streets found for calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                streetId = 0

                # try to find the configured and matching street
                for street in response:
                    if self._street in street["name"]:
                        streetId = street["id"]

                if streetId == 0:
                    _LOGGER.warning(
                        f"street '{self._street}' not found in calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                # HOUSENUMBER
                # get available housenumbers for calendar year
                
                params = {
                    "calendarId": calendarYearId,
                    "streetId": streetId,
                }

                url = f"{baseUrl}/housenumbers"
                response = requests.get(url, params=params)
                response.raise_for_status()

                # data validation
                response = response.json()
                if len(response) <= 0:
                    _LOGGER.warning(
                        f"no housenumbers found for calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                housenumberId = 0

                # try to find the configured and matching housenumber
                for housenumber in response:
                    if self._housenumber in housenumber:
                        housenumberId = self._housenumber

                if housenumberId == 0:
                    _LOGGER.warning(
                        f"housenumber '{self._housenumber}' not found in calendar year {calendarYearName}, continuing with next calendar year ..."
                    )
                    continue

                params = {
                    "calendarId": calendarYearId,
                    "cityId": cityId,
                    "streetId": streetId,
                    "housenumber": housenumberId,
                    "outputType": "ical",
                }

                # get ical data for year and city, street, housenumber
                url = f"{baseUrl}/v2/export"
                response = requests.get(url, params=params)
                response.raise_for_status()

                dates = self._ics.convert(response.text)

                for d in dates:
                    entries.append(Collection(d[0], d[1]))


        # validate that we processed some data and show an error if not
        if len(entries) <= 0:
            _LOGGER.warning(
                f"we were not able to get any waste entries for you! please file an issue at {issueUrl} and mention @dm82m and add this zone: '{self._zone}'"
            )

        return entries
