import datetime
import requests
import json

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Cubefour AWIDO"
DESCRIPTION = "Source for waste collections hosted by Cubefour."
URL = "https://www.awido-online.de/"

class Source:
    def __init__(self, customer, fraktionen, city, street, housenumber):
        self._customer = customer
        self._fractions = fractions
        self._city = city
        self._street = street
        self._housenumber = housenumber

    def fetch(self):
        # Retrieve list of places
        places = json.loads(requests.get(f'https://awido.cubefour.de//WebServices/Awido.Service.svc/secure/getPlaces/client={self._customer}').text)

        # Check if given place is in the list
        found_places = [(place['key'], place['value']) for place in places if place['value'] == self._city]
        if len(found_places) != 1:
            return []
        place_oid = found_places[0][0]

        streets = json.loads(requests.get(f'https://awido.cubefour.de//WebServices/Awido.Service.svc/secure/getGroupedStreets/{place_oid}?client={self._customer}').text)
        found_streets = [(street['key'], street['value']) for street in streets if self._street in street['value']]
        if len(found_streets) != 1:
            return []
        # If Housenumber is already in found street, oid is already found, if not, check for housenumber
        if self._street != found_streets[0][1]:
            oid = found_streets[0][0]
        else:
            street_oid = found_streets[0][0]
            housenumbers = json.loads(requests.get(f'https://awido.cubefour.de//WebServices/Awido.Service.svc/secure/getStreetAddons/{street_oid}?client={self._customer}').text)
            found_housenumbers = [(hn['key'], hn['value']) for hn in housenumbers if self._housenumber == hn['value']]
            if len(found_housenumbers) == 0:
                return []
            oid = found_housenumbers[0][0]

        cal_json = json.loads(requests.get(f'https://awido.cubefour.de//WebServices/Awido.Service.svc/secure/getData/{oid}?fractions={fraktionen}&client={self._customer}'))
        calendar = [item for item in cal_json['calendar'] if item['ad'] is not None]
        fracts = cal_json['fracts']
        fractions = {}
        for fract in fracts:
            fractions[fract['snm']] = fract['nm']
        
        entries = []
        for calitem in calendar:
            date = datetime.date(int(calitem['dt'][0:4]), int(calitem['dt'][4:6]), int(calitem['dt'][6:8]))
            for i, fracitem in calitem['fr']:
                typ = fractions[fracitem]
                entries.append(Collection(date, typ))
        
        return entries