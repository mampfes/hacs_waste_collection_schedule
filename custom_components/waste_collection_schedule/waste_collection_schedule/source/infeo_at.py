import json
import logging
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

_LOGGER = logging.getLogger(__name__)

TITLE = "INFEO"
DESCRIPTION = "Source for INFEO waste collection."
URL = "https://www.infeo.at/"
TEST_CASES = {"Bogenschütz": {"customer": "bogenschütz", "zone": "Dettenhausen"}}


class Source:
    def __init__(self, customer, zone):
        self._customer = customer
        self._zone = zone
        self._ics = ICS()

    def fetch(self):
        baseUrl = f"https://services.infeo.at/awm/api/{self._customer}/wastecalendar"
        issueUrl = "https://github.com/mampfes/hacs_waste_collection_schedule/issues/new"
    
        params = {
            "showUnpublishedCalendars": "false",
        }
    
        # get the available published calendar years
        url = f"{baseUrl}/calendars"
        response = requests.get(url, params=params)

        # data validation
        if(response.status_code != 200):
            _LOGGER.error(f"problems during api calendar year access, please file an issue at {issueUrl} and mention @dm82m and add this: {response.text}")
            return []
            
        response = response.json()
        if len(response) <= 0:
            _LOGGER.error(f"no calendars found, please file an issue at {issueUrl} and mention @dm82m")
            return []

        entries = []

        # loop over each calendar year entry and extract data
        for calendarYear in response:
            calendarYearId = calendarYear["id"]
            calendarYearName = calendarYear["name"]

            params = {
                "calendarId": calendarYearId,
            }

            # get available zones for calendar year
            url = f"{baseUrl}/zones"
            response = requests.get(url, params=params)

            # data validation
            if(response.status_code != 200):
                _LOGGER.error(f"problems during api zones for calendar year access, please file an issue at {issueUrl} and mention @dm82m and add this: {response.text}")
                return []
                
            response = response.json()
            if len(response) <= 0:
                _LOGGER.warning(f"no zones found for calendar year {calendarYearName}, continuing with next calendar year ...")
                continue

            zoneId = 0

            # try to find the configured and matching zone
            for zone in response:
                if self._zone in zone["name"]:
                    zoneId = zone["id"]

            if zoneId == 0:
                _LOGGER.warning(f"zone '{self._zone}' not found in calendar year {calendarYearName}, continuing with next calendar year ...")
                continue

            params = {
                "calendarId": calendarYearId,
                "zoneId": zoneId,
                "outputType": "ical",
            }

            # get ical data for year and zone
            url = f"{baseUrl}/v2/export"
            response = requests.get(url, params=params)

            # data validation
            if(response.status_code != 200):
                _LOGGER.error(f"problems during api ical data for zone in calendar year, please file an issue at {issueUrl} and mention @dm82m and add this: {response.text}")
                return []

            dates = self._ics.convert(response.text)

            for d in dates:
                entries.append(Collection(d[0], d[1]))
        
        # validate that we processed some data and show an error if not
        if len(entries) <= 0:
            _LOGGER.error(f"we were not able to get any waste entries for you! please file an issue at {issueUrl} and mention @dm82m and add this zone: '{self._zone}'")
        
        return entries
