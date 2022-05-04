import datetime
from waste_collection_schedule import Collection

from datetime import datetime
import requests
import logging
import typing

TITLE = 'Warszawa19115.pl'
DESCRIPTION = "Source for Warsaw city garbage collection" 
URL = "https://warszawa19115.pl/harmonogramy-wywozu-odpadow"
TEST_CASES = {
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
    OC_URL = 'https://warszawa19115.pl/harmonogramy-wywozu-odpadow'
    OC_PARAMS = {
        'p_p_id': 'portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ',
        'p_p_lifecycle': 2,
        'p_p_resource_id': ''
    }
    OC_HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': ''
    }

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
            geolocation_request = geolocation_session.get(self.OC_URL)
            geolocation_request.raise_for_status()

            # Calendar call requires 'autocompleteResourceURL' param to work
            self.OC_HEADERS['Cookie'] = str(geolocation_request.cookies)
            self.OC_PARAMS['p_p_resource_id'] = 'autocompleteResourceURL'
            
            # Search for geolocation ID
            geolocation_response = requests.request("POST", self.OC_URL, headers=self.OC_HEADERS, params=self.OC_PARAMS, data=payload.encode('utf-8'))
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
        calendar_request = calendar_session.get(self.OC_URL)
        calendar_request.raise_for_status()

        # Calendar call requires 'ajaxResourceURL' param to work
        self.OC_HEADERS['Cookie'] = str(calendar_request.cookies)
        self.OC_PARAMS['p_p_resource_id'] = 'ajaxResourceURL'

        calendar_request = requests.request("POST", self.OC_URL, data=payload, headers=self.OC_HEADERS, params=self.OC_PARAMS)
        calendar_request.raise_for_status()

        calendar_result = calendar_request.json()
        _LOGGER.debug(f"Calendar response: {calendar_result!r}")

        if 'success' in calendar_result and not calendar_result['success']:
            raise SourceParseError('Unspecified server-side error when getting calendar')

        if len(calendar_result) < 0 or not calendar_result[0]["harmonogramy"] or len(calendar_result[0]["harmonogramy"]) < 0:
            raise SourceParseError('Expected list of dates from calendar search, got empty or missing list')
        
        entries = []

        map_name = {
            'BG': 'Bio restauracyjne',
            'BK': 'Bio',
            'MT': 'Metale i tworzywa sztuczne',
            'OP': 'Papier',
            'OS': 'Szkło',
            'OZ': 'Zielone',
            'WG': 'Odpady wielkogabarytowe',
            'ZM': 'Odpady zmieszane'
        }

        for result in calendar_result:
            for entry in result['harmonogramy']:
                if entry['data']:
                    waste_type = map_name[entry['frakcja']['id_frakcja']]
                    waste_date = datetime.strptime(entry['data'], '%Y-%m-%d')
                    entries.append(Collection(waste_date,waste_type))

        return entries