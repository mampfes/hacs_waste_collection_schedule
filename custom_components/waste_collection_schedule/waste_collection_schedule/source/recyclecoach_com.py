
import requests
import json

from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Recycle Coach"
DESCRIPTION = "Source loader for recyclecoach.com"
URL = "https://recyclecoach.com"
COUNTRY = "us"

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Yard Waste": "mdi:leaf",
}

EXTRA_INFO = [
    {
        "title": "Albuquerque, New Mexico, USA",
        "url": "https://recyclecoach.com/cities/usa-nm-city-of-albuquerque/"
    },
    {
        "title": "Tucson, Arizona, USA",
        "url": "https://recyclecoach.com/cities/usa-az-city-of-tucson/"
    },
    {
        "title": "Olympia, Washington, USA",
        "url": "https://recyclecoach.com/cities/usa-wa-city-of-olympia/"
    },
    {
        "title": "Newark, Delaware, USA",
        "url": "https://recyclecoach.com/cities/usa-de-city-of-newark/"
    },
    {
        "title": "Louisville, Kentucky, USA",
        "url": "https://recyclecoach.com/cities/usa-ky-city-of-louisville/"
    }
]

TEST_CASES = {
        "Default": {
            "street": "2242 grinstead drive",
            "city": "louisville",
            "state": "KY"
            },
        "Problematic City Lookup": {
            "street": "2202 E Florence Dr",
            "city": "Tucson",
            "state": "AZ",
            "district_id": "TUC",
            "project_id": "532"
            },
        "olympia": {
            "street": "1003 Lybarger St NE",
            "city": "Olympia",
            "state": "Washington"
            },
        "newark": {
            "street": "24 Townsend Rd",
            "city": "Newark",
            "state": "Delaware"
            },
        "albuquerque": {
            "street": "1505 Silver Ave SE",
            "city": "Albuquerque",
            "state": "New Mexico"
            },
}


class Source:
    def __init__(self, street, city, state, project_id=None, district_id=None, zone_id=None):  # argX correspond to the args dict in the source configuration
        self.street = self._format_key(street)
        self.city = self._format_key(city)
        self.state = self._format_key(state)
        self.project_id = self._format_key(project_id) if project_id else None
        self.district_id = self._format_key(district_id) if district_id else None

        self.zone_id = zone_id # uses lowercase z's, not sure if matters
        self.stage = 0

    def _format_key(self, param):
        """ Get rid of ambiguity in caps/spacing """
        return param.upper().strip()

    def _lookup_city(self):
        city_finder = 'https://recyclecoach.com/wp-json/rec/v1/cities?find={}, {}'.format(self.city, self.state)
        res = requests.get(city_finder)
        city_data = res.json()

        if len(city_data['cities']) == 1:
            self.project_id = city_data['cities'][0]['project_id']
            self.district_id = city_data['cities'][0]['district_id']
            self.stage = float(city_data['cities'][0]['stage'])

            if self.stage < 3:
                raise Exception("Found your city, but it is not yet supported fully by recycle coach.")

        elif len(city_data['cities']) > 1:

            for city in city_data['cities']:
                if city['city_nm'].upper() == self.city.upper():
                    self.project_id = city['project_id']
                    self.district_id = city['district_id']
                    self.stage = float(city['stage'])
                    return True

            # not sure what to do with ambiguity here
            # print(json.dumps(city_data['cities'], indent=4))
            raise Exception("Could not determine district or project, Debug here to find your discrict and project_id")

    def _lookup_zones(self):
        zone_finder = 'https://api-city.recyclecoach.com/zone-setup/address?sku={}&district={}&prompt=undefined&term={}'.format(self.project_id, self.district_id, self.street)
        res = requests.get(zone_finder)
        zone_data = res.json()
        for zone_res in zone_data['results']:
            if ',' in zone_res['address']:
                streetpart, _ = self._format_key(zone_res['address']).split(",")
            else:
                streetpart = self._format_key(zone_res['address'])

            if streetpart in self.street:
                self.zone_id = self._build_zone_string(zone_res['zones'])
                return self.zone_id

        raise Exception("Unable to find zone")

    def _build_zone_string(self, z_match):
        """ takes matching json and builds a format zone-z12312-z1894323-z8461 """
        zone_str = "zone"

        for zonekey in z_match:
            zone_str += "-{}".format(z_match[zonekey])

        return zone_str

    def fetch(self):
        """Builds the date fetching request through looking up address on separate endpoints, will skip these requests if you can provide the district_id, project_id and/or zone_id
        """

        if not self.project_id or not self.district_id:
            self._lookup_city()

        if not self.zone_id:
            self._lookup_zones()

        collection_def_url = 'https://reg.my-waste.mobi/collections?project_id={}&district_id={}&zone_id={}&lang_cd=en_US'.format(self.project_id, self.district_id, self.zone_id)
        schedule_url = 'https://pkg.my-waste.mobi/app_data_zone_schedules?project_id={}&district_id={}&zone_id={}'.format(self.project_id, self.district_id, self.zone_id)

        collection_def = None
        schedule_def = None
        collection_types = None

        response = requests.get(collection_def_url)
        collection_def = json.loads(response.text)

        response = requests.get(schedule_url)
        schedule_def = json.loads(response.text)

        collection_types = collection_def["collection"]["types"]

        entries = []
        date_format = "%Y-%m-%d"

        for year in schedule_def["DATA"]:
            for month in year["months"]:
                for event in month["events"]:
                    for collection in event["collections"]:
                        ct = collection_types["collection-" + str(collection["id"])]
                        c = Collection(
                            datetime.strptime(event["date"], date_format).date(),
                            ct["title"],
                            ICON_MAP.get(ct["title"]),
                        )
                        entries.append(c)


        return entries
