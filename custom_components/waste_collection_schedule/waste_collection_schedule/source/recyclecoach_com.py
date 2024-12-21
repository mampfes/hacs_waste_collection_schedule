import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

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
        "url": "https://recyclecoach.com/cities/usa-nm-city-of-albuquerque/",
        "default_params": {"city": "Albuquerque", "state": "New Mexico"},
    },
    {
        "title": "Tucson, Arizona, USA",
        "url": "https://recyclecoach.com/cities/usa-az-city-of-tucson/",
        "default_params": {"city": "Tucson", "state": "Arizona"},
    },
    {
        "title": "Olympia, Washington, USA",
        "url": "https://recyclecoach.com/cities/usa-wa-city-of-olympia/",
        "default_params": {"city": "Olympia", "state": "Washington"},
    },
    {
        "title": "Tacoma, Washington, USA",
        "url": "https://recyclecoach.com/cities/usa-wa-city-of-tacoma/",
        "default_params": {"city": "Tacoma", "state": "Washington"},
    },
    {
        "title": "Newark, Delaware, USA",
        "url": "https://recyclecoach.com/cities/usa-de-city-of-newark/",
        "default_params": {"city": "Newark", "state": "Delaware"},
    },
    {
        "title": "Louisville, Kentucky, USA",
        "url": "https://recyclecoach.com/cities/usa-ky-city-of-louisville/",
        "default_params": {"city": "Louisville", "state": "Kentucky"},
    },
    {
        "title": "London (ON)",
        "url": "https://london.ca/",
        "country": "ca",
        "default_params": {"city": "London", "state": "Ontario"},
    },
    {
        "title": "Aurora (ON)",
        "url": "https://www.aurora.ca/",
        "country": "ca",
        "default_params": {"city": "Aurora", "state": "Ontario"},
    },
    {
        "title": "Vaughan (ON)",
        "url": "https://www.vaughan.ca/",
        "country": "ca",
        "default_params": {"city": "Vaughan", "state": "Ontario"},
    },
    {
        "title": "Richmond Hill (ON)",
        "url": "https://www.richmondhill.ca/",
        "country": "ca",
    },
    {
        "title": "Kawartha Lakes (ON)",
        "url": "https://www.kawarthalakes.ca/",
        "country": "ca",
        "default_params": {"city": "Kawartha Lakes", "state": "Ontario"},
    },
    {
        "title": "Norfolk County (ON)",
        "url": "https://www.norfolkcounty.ca/",
        "country": "ca",
    },
]

TEST_CASES = {
    "Default": {"street": "2242 grinstead drive", "city": "louisville", "state": "KY"},
    "Problematic City Lookup": {
        "street": "2202 E Florence Dr",
        "city": "Tucson",
        "state": "AZ",
        "district_id": "TUC",
        "project_id": "532",
    },
    "olympia": {
        "street": "1003 Lybarger St NE",
        "city": "Olympia",
        "state": "Washington",
    },
    "newark": {"street": "24 Townsend Rd", "city": "Newark", "state": "Delaware"},
    "albuquerque": {
        "street": "1505 Silver Ave SE",
        "city": "Albuquerque",
        "state": "New Mexico",
    },
    "london ontario": {
        "street": "1065 Sunningdale Rd E",
        "city": "London",
        "state": "Ontario",
    },
    "london ontario with districtID": {
        "street": "1065 Sunningdale Rd E",
        "city": "London",
        "state": "Ontario",
        "project_id": "528",
        "district_id": "CityofLondon",
        "zone_id": "zone-z547",
    },
    "aurora ontario": {
        "street": "123 Cranberry Lane",
        "city": "Aurora",
        "state": "Ontario",
    },
    "Vaughan, Ontario, Canada": {  # https://app.my-waste.mobi/widget/576-Vaughan/home.php
        "street": "Main St",
        "city": "Vaughan",
        "state": "Ontario",
    },
    "67 Baseline Rd Coboconk, ON": {
        "street": "67 Baseline Rd",
        "city": "Coboconk",
        "state": "Ontario",
    },
    "Richmond Hill, Ontario, Canada": {
        "street": "MOONLIGHT lane",
        "city": "Richmond Hill",
        "state": "Ontario",
    },
    "Norfolk County, Ontario, Canada (with district_id, project_id & zone_id)": {
        "district_id": "OLYMP",
        "project_id": 3107,
        "zone_id": "zone-z11266-z16205-z16208-z16218",
    },
}


class Source:
    def __init__(
        self,
        street=None,
        city=None,
        state=None,
        project_id=None,
        district_id=None,
        zone_id=None,
    ):  # argX correspond to the args dict in the source configuration
        self.street = self._format_key(street)
        self.city = self._format_key(city)
        self.state = self._format_key(state)
        self.project_id = self._format_key(project_id) if project_id else None
        self.district_id = str(district_id).strip() if district_id else None

        self.zone_id = zone_id  # uses lowercase z's, not sure if matters
        self.stage = 0

    def _format_key(self, param):
        """Get rid of ambiguity in caps/spacing."""
        return str(param).upper().strip()

    def _lookup_city(self):
        city_finder = f"https://api-city.recyclecoach.com/city/search?term={self.city}, {self.state}"
        res = requests.get(city_finder)
        city_data = res.json()

        if len(city_data) == 1:
            self.project_id = city_data[0]["project_id"]
            self.district_id = city_data[0]["district_id"]
            self.stage = float(city_data[0]["stage"])

            if self.stage < 3:
                raise Exception(
                    "Found your city, but it is not yet supported fully by recycle coach."
                )
            return

        elif len(city_data) > 1:
            for city in city_data:
                if city["city_nm"].upper() == self.city.upper():
                    self.project_id = city["project_id"]
                    self.district_id = city["district_id"]
                    self.stage = float(city["stage"])
                    return

        raise Exception(
            "Could not determine district or project, This probably means your city, state is wrong or not supported."
        )

    def _lookup_zones_with_geo(self):
        pos_finder = f"https://api-city.recyclecoach.com/geo/address?address={self.street}&project_id={self.project_id}&district_id={self.district_id}"
        res = requests.get(pos_finder)
        lat = None
        pos_data = res.json()
        streets = []
        for pos_res in pos_data:
            streetpart = self._format_key(pos_res["address"]).split(",")[0]
            streets.append(pos_res["address"].strip().split(",")[0])

            if streetpart in self.street:
                lat = pos_res["lat"]
                lng = pos_res["lng"]
                break

        if not lat:
            if streets:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street",
                    self.street,
                    streets,
                )
            raise SourceArgumentNotFound(
                "street",
                self.street,
            )

        zone_finder = f"https://pkg.my-waste.mobi/get_zones?project_id={self.project_id}&district_id={self.district_id}&lat={lat}&lng={lng}"
        res = requests.get(zone_finder)
        zone_data = {z["prompt_id"]: "z" + z["zone_id"] for z in res.json()}
        self.zone_id = self._build_zone_string(zone_data)

        return self.zone_id

    def _lookup_zones(self):
        zone_finder = f"https://api-city.recyclecoach.com/zone-setup/address?sku={self.project_id}&district={self.district_id}&prompt=undefined&term={self.street}"
        res = requests.get(zone_finder)
        zone_data = res.json()
        if "results" not in zone_data:
            return self._lookup_zones_with_geo()
        streets = []
        for zone_res in zone_data["results"]:
            streetpart = self._format_key(zone_res["address"]).split(",")[0]
            streets.append(zone_res["address"].strip().split(",")[0])
            if streetpart in self.street:
                self.zone_id = self._build_zone_string(zone_res["zones"])
                return self.zone_id
        if streets:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self.street,
                streets,
            )
        raise SourceArgumentNotFound(
            "street",
            self.street,
        )

    def _build_zone_string(self, z_match):
        """Take matching json and build a format zone-z12312-z1894323-z8461."""
        zone_str = "zone"

        for zonekey in z_match:
            zone_str += f"-{z_match[zonekey]}"

        return zone_str

    def fetch(self):
        """Build the date fetching request through looking up address on separate endpoints, skip these requests if you can provide the district_id, project_id and/or zone_id."""
        if not self.project_id or not self.district_id:
            self._lookup_city()

        if not self.zone_id:
            self._lookup_zones()

        collection_def_url = f"https://reg.my-waste.mobi/collections?project_id={self.project_id}&district_id={self.district_id}&zone_id={self.zone_id}&lang_cd=en_US"
        schedule_url = f"https://pkg.my-waste.mobi/app_data_zone_schedules?project_id={self.project_id}&district_id={self.district_id}&zone_id={self.zone_id}"

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
                        if collection["status"] == "is_none":
                            continue
                        ct = collection_types["collection-" + str(collection["id"])]
                        c = Collection(
                            datetime.strptime(event["date"], date_format).date(),
                            ct["title"],
                            ICON_MAP.get(ct["title"]),
                        )
                        entries.append(c)
        return entries
