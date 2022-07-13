import logging
import re
import typing
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection


TITLE = 'Melton City Council'
DESCRIPTION = 'Source for Melton City Council rubbish collection.'
URL = 'https://www.melton.vic.gov.au/My-Area'
TEST_CASES = {
    'Tuesday A': {'street_address': '23 PILBARA AVENUE BURNSIDE 3023'},
    'Tuesday A Geolocation ID': {'geolocation_id': '00faf1f7-9aa0-4b2c-a9b9-54c29401e68c'},
    'Tuesday B': {'street_address': '29 COROWA CRESCENT BURNSIDE 3023'},
    'Thursday A': {'street_address': '2 ASPIRE BOULEVARD FRASER RISE 3336'},
    'Thursday B': {'street_address': '17 KEYNES CIRCUIT FRASER RISE 3336'}
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
    OC_GEOLOCATION_SEARCH_URL = 'https://www.melton.vic.gov.au/api/v1/myarea/search'

    OC_SESSION_URL = 'https://www.melton.vic.gov.au/My-Area'
    OC_CALENDAR_URL = 'https://www.melton.vic.gov.au/ocapi/Public/myarea/wasteservices'

    OC_RE_DATE_STR = re.compile(r'[^\s]+\s(\d{1,2}/\d{1,2}/\d{4})')

    def __init__(self, street_address: typing.Optional[str] = None, geolocation_id: typing.Optional[str] = None):
        if street_address is None and geolocation_id is None:
            raise SourceConfigurationError('Either street_address or geolocation_id must have a value')

        self._street_address = street_address
        self._geolocation_id = geolocation_id

    @property
    def geolocation_id(self) -> str:
        if self._geolocation_id is None:
            # Search for geolocation ID
            geolocation_response = requests.get(
                self.OC_GEOLOCATION_SEARCH_URL,
                params={
                    'keywords': self._street_address,
                    'maxresults': 1
                }
            )
            geolocation_response.raise_for_status()

            # Pull ID from results
            geolocation_result = geolocation_response.json()
            _LOGGER.debug(f"Search response: {geolocation_response!r}")

            if 'success' in geolocation_result and not geolocation_result['success']:
                raise SourceParseError('Unspecified server-side error when searching address')

            if 'Items' not in geolocation_result or \
                    geolocation_result['Items'] is None or \
                    len(geolocation_result['Items']) < 1:
                raise SourceParseError('Expected list of locations from address search, got empty or missing list')

            geolocation_data = geolocation_result['Items'][0]

            if 'Id' not in geolocation_data:
                raise SourceParseError('Location in address search result but missing geolocation ID')

            self._geolocation_id = geolocation_data['Id']
            _LOGGER.info(f"Address {self._street_address} mapped to geolocation ID {self._geolocation_id}")

        return self._geolocation_id

    def fetch(self) -> typing.List[Collection]:
        # Calendar lookup cares about a cookie, so a Session must be used
        calendar_session = requests.Session()

        calendar_request = calendar_session.get(self.OC_SESSION_URL)
        calendar_request.raise_for_status()

        calendar_request = calendar_session.get(
            self.OC_CALENDAR_URL,
            params={
                'geolocationid': self.geolocation_id,
                'ocsvclang': 'en-AU'
            }
        )
        calendar_request.raise_for_status()

        calendar_result = calendar_request.json()
        _LOGGER.debug(f"Calendar response: {calendar_result!r}")

        if 'success' in calendar_result and not calendar_result['success']:
            raise SourceParseError('Unspecified server-side error when getting calendar')

        # Extract entries from bundled HTML
        calendar_parser = BeautifulSoup(calendar_result['responseContent'], 'html.parser')

        pickup_entries = []

        for element in calendar_parser.find_all('article'):
            _LOGGER.debug(f"Parsing collection: {element!r}")

            waste_type = element.h3.string

            # Extract and parse collection date
            waste_date_match = self.OC_RE_DATE_STR.match(element.find(class_='next-service').string.strip())

            if waste_date_match is None:
                continue

            waste_date = datetime.strptime(waste_date_match[1], '%d/%m/%Y').date()

            # Base icon on type
            waste_icon = ICON_MAP.get(waste_type.lower(), 'mdi:trash-can')

            pickup_entries.append(Collection(waste_date, waste_type, waste_icon))
            _LOGGER.info(f"Collection for {waste_type} (icon: {waste_icon}) on {waste_date}")

        return pickup_entries
