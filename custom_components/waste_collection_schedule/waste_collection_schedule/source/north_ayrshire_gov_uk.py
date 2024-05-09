import json
from urllib.parse import parse_qs, urlparse

import requests
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Ayrshire Council"
DESCRIPTION = "Source for north-ayrshire.gov.uk services for North Ayrshire"
URL = "https://www.north-ayrshire.gov.uk/"
API_URL = "https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/YourLocationLive/MapServer/8/query?f=json&outFields=*&returnDistinctValues=true&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=UPRN%20%3D%20%27{0}%27"

TEST_CASES = {
    "Test_001": {"uprn": 126043248},
    "Test_002": {"uprn": 126021147},
    "Test_003": {"uprn": 126091148},
}

ICON_MAP = {
    "Grey": "mdi:trash-can",
    "Brown": "mdi:leaf",
    "Purple": "mdi:glass-fragile",
    "Blue": "mdi:recycle",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        return self.__get_bin_collection_info_json(self._uprn)

    def __get_bin_collection_info_json(self, uprn):
        r = requests.get(API_URL.format(uprn))
        bin_json = r.json()['features']
        bin_list = []
        if 'BLUE_DATE_TEXT' in bin_json[0]['attributes']:
            bin_list.append(["Blue","/".join(reversed(bin_json[0]['attributes']['BLUE_DATE_TEXT'].split("/")))])
        if 'GREY_DATE_TEXT' in bin_json[0]['attributes']:
            bin_list.append(["Grey","/".join(reversed(bin_json[0]['attributes']['GREY_DATE_TEXT'].split("/")))])
        if 'PURPLE_DATE_TEXT' in bin_json[0]['attributes']:
            bin_list.append(["Purple","/".join(reversed(bin_json[0]['attributes']['PURPLE_DATE_TEXT'].split("/")))])
        if 'BROWN_DATE_TEXT' in bin_json[0]['attributes']:
            bin_list.append(["Brown","/".join(reversed(bin_json[0]['attributes']['BROWN_DATE_TEXT'].split("/")))])

        entries = []
        for bins in bin_list:
            entries.append(
                Collection(
                    date=parser.parse(bins[1]).date(),
                    t=bins[0],
                    icon=ICON_MAP.get(bins[0]),
                )
            )
        return entries