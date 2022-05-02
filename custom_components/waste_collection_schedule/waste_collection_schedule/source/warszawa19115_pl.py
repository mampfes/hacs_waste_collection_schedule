import datetime
from waste_collection_schedule import Collection

import requests
import json
import logging
import typing
import re

TITLE = 'Warszawa19115.pl'
DESCRIPTION = "Source for Warsaw city garbage collection"  # Describe your source
URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow"    # Insert url to service homepage
TEST_CASES = { # Insert arguments for test cases using test_sources.py script
    "Street Name": {"street_address": "MARSZAŁKOWSKA 84/92, 00-514 Śródmieście"},
    'Geolocation ID': {'geolocation_id': '76802934'},
}

_LOGGER = logging.getLogger(__name__)

ICON_MAP = {
    'green waste': 'mdi:leaf',
    'recycling': 'mdi:recycle'
}


class SourceConfigurationError(ValueError):
    pass


class SourceParseError(ValueError):
    pass



class Source:
    OC_GEOLOCATION_SEARCH_URL = 'https://warszawa19115.pl/harmonogramy-wywozu-odpadow?p_p_id=portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=autocompleteResourceURL&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1'

    OC_SESSION_URL = 'https://warszawa19115.pl/harmonogramy-wywozu-odpadow'
    OC_CALENDAR_URL = 'https://warszawa19115.pl/harmonogramy-wywozu-odpadow?p_p_id=portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=ajaxResourceURL&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1'

    OC_RE_DATE_STR = re.compile(r'[^\s]+\s(\d{1,2}/\d{1,2}/\d{4})')

    def __init__(self, street_address: typing.Optional[str] = None, geolocation_id: typing.Optional[str] = None):
        if street_address is None and geolocation_id is None:
            raise SourceConfigurationError('Either street_address or geolocation_id must have a value')

        self._street_address = street_address
        self._geolocation_id = geolocation_id

    @property
    def geolocation_id(self) -> str:
        if self._geolocation_id is None:
            payload='_portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ_name=' + self._street_address
            geolocation_session = requests.Session()
            geolocation_request = geolocation_session.get(self.OC_SESSION_URL)
            geolocation_request.raise_for_status()
            headers = {
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'Accept': 'application/json, text/javascript, */*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'Cookie': str(geolocation_request.cookies)
            }
            # Search for geolocation ID
            geolocation_response = requests.request("POST", self.OC_GEOLOCATION_SEARCH_URL, headers=headers, data=payload.encode('utf-8'))
            geolocation_response.raise_for_status()

            # Pull ID from results
            geolocation_result = geolocation_response.json()
            _LOGGER.debug(f"Search response: {geolocation_response!r}")

            if 'success' in geolocation_result and not geolocation_result['success']:
                raise SourceParseError('Unspecified server-side error when searching address')

            if len(geolocation_result) < 1:
                raise SourceParseError('Expected list of locations from address search, got empty or missing list')

            geolocation_data = geolocation_result[0]

            if 'addressPointId' not in geolocation_data:
                raise SourceParseError('Location in address search result but missing geolocation ID')

            self._geolocation_id = geolocation_data['addressPointId']
            _LOGGER.info(f"Address {self._street_address} mapped to geolocation ID {self._geolocation_id}")
            print(f"Address {self._street_address} mapped to geolocation ID {self._geolocation_id}")

        return self._geolocation_id

    def fetch(self):
        # Calendar lookup cares about a cookie, so a Session must be used
        payload='_portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ_addressPointId=' + str(self.geolocation_id)
        calendar_session = requests.Session()
        calendar_request = calendar_session.get(self.OC_SESSION_URL)
        calendar_request.raise_for_status()

        headers = {
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'Accept': 'application/json, text/javascript, */*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'host': 'warszawa19115.pl',
            'Cookie': str(calendar_request.cookies)
        }

        calendar_request = requests.request("POST", self.OC_CALENDAR_URL, data=payload, headers=headers)
        calendar_request.raise_for_status()

        calendar_result = calendar_request.json()
        _LOGGER.debug(f"Calendar response: {calendar_result!r}")

        if 'success' in calendar_result and not calendar_result['success']:
            raise SourceParseError('Unspecified server-side error when getting calendar')

        if len(calendar_result) < 0 or not calendar_result[0]["harmonogramy"] or len(calendar_result[0]["harmonogramy"]) < 0:
            raise SourceParseError('Expected list of dates from calendar search, got empty or missing list')
        
        entries = []

        for entry in calendar_result[0]["harmonogramy"]:
            if entry["data"]:
                entries.append(
                    Collection(
                        datetime.datetime.strptime(entry["data"], "%Y-%m-%d"),
                        entry["frakcja"]["nazwa"],
                    )
                )

        print(entries)

        return entries