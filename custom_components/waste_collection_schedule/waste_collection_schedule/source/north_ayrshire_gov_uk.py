import requests
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Ayrshire Council"
DESCRIPTION = "Source for north-ayrshire.gov.uk services for North Ayrshire"
URL = "https://www.north-ayrshire.gov.uk/"
API_URL = "https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/YourLocationLive/MapServer/8/query?f=json&outFields=*&returnDistinctValues=true&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=UPRN%20%3D%20%27{0}%27"

TEST_CASES = {
    "Test_001": {"uprn": "126043248"},
    "Test_002": {"uprn": 126021147},
    "Test_003": {"uprn": 126091148},
    "Test_004": {"uprn": "126000270"},
}

ICON_MAP = {
    "Grey": "mdi:trash-can",
    "Brown": "mdi:leaf",
    "Purple": "mdi:glass-fragile",
    "Blue": "mdi:recycle",
}

BIN_TEXTS = [
    "BLUE_DATE_TEXT",
    "GREY_DATE_TEXT",
    "PURPLE_DATE_TEXT",
    "BROWN_DATE_TEXT",
]


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        return self.__get_bin_collection_info_json(self._uprn)

    def __get_bin_collection_info_json(self, uprn):
        r = requests.get(API_URL.format(uprn))
        bin_json = r.json()["features"]
        bin_list = []
        for item in BIN_TEXTS:
            if item in bin_json[0]["attributes"]:
                colour = item.split("_")[0].capitalize()
                try:
                    bin_list.append(
                        [
                            colour,
                            "/".join(
                                reversed(bin_json[0]["attributes"][item].split("/"))
                            ),
                        ]
                    )
                except AttributeError:  # catches error when no date is present
                    pass

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
