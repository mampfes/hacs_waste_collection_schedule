import datetime
import requests
import json

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Cubefour AWIDO"
DESCRIPTION = "Source for waste collections hosted by Cubefour."
URL = "https://www.awido-online.de/"
TEST_CASES = {
    "Schorndorf, Raingrund 21": {
        "customer": "rmk",
        "city": "Schorndorf",
        "street": "Raingrund",
        "housenumber": "21",
        "fraktionen": "1"
    },
#    "Altomünster, Maisbrunn": {
#        "customer": "lra-dah",
#        "city": "Altomünster",
#        "street": "Maisbrunn",
#        "fraktionen": "1,3"
#    },
#    "SOK-Alsmannsdorf": {
#        "customer": "zaso",
#        "city": "SOK-Alsmannsdorf",
#        "fraktionen": "1,2,3,10"
#    },
#    "Kaufbeuren, Rehgrund": {
#        "customer": "kaufbeuren",
#        "city": "Kaufbeuren",
#        "street": "Rehgrund",
#        "fraktionen": "1,3,4"
#    }
}

class Source:
    def __init__(self, customer, city, street=None, housenumber=None, fraktionen=None):
        self._customer = customer
        self._fraktionen = fraktionen
        self._city = city
        self._street = street
        self._housenumber = housenumber

    def fetch(self):
        # Retrieve list of places
        r = requests.get(f'https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getPlaces/client={self._customer}')
        places = json.loads(r.text)

        # Check if given place is in the list
        found_places = [(place['key'], place['value']) for place in places if place['value'] == self._city]
        if len(found_places) != 1:
            return []
        if self._street is None:
            oid = found_places[0][0]
        else:
            place_oid = found_places[0][0]

            r = requests.get(f'https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getGroupedStreets/{place_oid}', params={"client":self._customer})
            streets = json.loads(r.text)

            found_streets = [(street['key'], street['value']) for street in streets if self._street in street['value']]
            if len(found_streets) != 1:
                return []
            # If Housenumber is already in found street, oid is already found, if not, check for housenumber
            if self._street != found_streets[0][1] or self._housenumber is None:
                oid = found_streets[0][0]
            else:
                street_oid = found_streets[0][0]
                r = requests.get(f'https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getStreetAddons/{street_oid}', params={"client":self._customer})
                housenumbers = json.loads(r.text)
                found_housenumbers = [(hn['key'], hn['value']) for hn in housenumbers if str(self._housenumber) == hn['value']]
                if len(found_housenumbers) == 0:
                    return []
                oid = found_housenumbers[0][0]

        r = requests.get(f'https://awido.cubefour.de/WebServices/Awido.Service.svc/secure/getData/{oid}', params={
            "fractions": str(self._fraktionen) if self._fraktionen is not None else "",
            "client":self._customer})
        cal_json = json.loads(r.text)
        calendar = [item for item in cal_json['calendar'] if item['ad'] is not None]
        fracts = cal_json['fracts']
        fractions = {}
        for fract in fracts:
            fractions[fract['snm']] = fract['nm']
        
        entries = []
        for calitem in calendar:
            date = datetime.date(int(calitem['dt'][0:4]), int(calitem['dt'][4:6]), int(calitem['dt'][6:8]))
            for fracitem in calitem['fr']:
                typ = fractions[fracitem]
                entries.append(Collection(date, typ))
        
        return entries