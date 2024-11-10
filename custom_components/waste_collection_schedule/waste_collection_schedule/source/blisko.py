from waste_collection_schedule import Collection

from string import Template
import urllib.request
import datetime
import json
import logging

TITLE = "Blisko"
DESCRIPTION = "Source script for Blisko APP"
URL = "https://gateway.sisms.pl"
COUNTRY = "pl"
TEST_CASES = {
    "Grzepnica/Rezydencka": {"ownerId": "112", "cityId": "0774204",
                             "streetId": "42719", "houseId": "32"}
}

API_URL = "https://abc.com/search/"

ICON_MAP = {
    "Zmieszane odpady komunalne": "mdi:trash-can",
    "Papier i tektura": "mdi:recycle",
    "Odpady biodegradowalne": "mdi:leaf",
}

# Arguments affecting the configuration GUI #


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "See blisko.md for help",
    "pl": "Zobacz w blisko.md"
}

PARAM_DESCRIPTIONS = {
    "en": {
        "ownerId": "ID of instance owner",
        "cityId": "City ID. Must include leading zeros if present",
        "streetId": "Street ID. Must include leading zeros if present ",
        "houseId": "House number. Must include leading zeros if present",
    }
}


def find_bin_name(binId, json):
    for entry in json:
        if entry['id'] == binId:
            return entry['name']
    raise Exception


schedule_url_template = Template(
    "https://gateway.sisms.pl/akun/api/owners/${ownerId}/timetable/get?\
unitId=32:11:01:2:${cityId}:${streetId}:${houseId}")


bins_url_template = Template(
    "https://gateway.sisms.pl/akun/api/owners/${ownerId}/bins/list?\
unitId=32:11:01:2:${cityId}:${streetId}:${houseId}")

_LOGGER = logging.getLogger(__name__)


class Source:
    # argX correspond to the args dict in the source configuration
    def __init__(self, ownerId: str, cityId: str, streetId: str,
                 houseId: str):
        self._ownerId = ownerId
        self._schedule_url = schedule_url_template.safe_substitute(
            ownerId=ownerId, cityId=cityId, streetId=streetId, houseId=houseId)
        self._bins_url = bins_url_template.safe_substitute(
            ownerId=ownerId, cityId=cityId, streetId=streetId, houseId=houseId)

    def fetch(self):

        entries = []  # List that holds collection schedule

        bins_data = urllib.request.urlopen(self._bins_url)
        bins = json.load(bins_data)['data']
        _LOGGER.warn(bins)
        timetable_data = urllib.request.urlopen(self._schedule_url)
        timetable_json = json.load(timetable_data)["data"]

        for month_data in timetable_json:
            for reception in month_data['receptions']:
                bin_name = find_bin_name(binId=reception['binId'], json=bins)
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(
                            reception['date'], '%Y-%m-%d').date(),
                        t=bin_name,
                        icon=ICON_MAP.get(bin_name),
                    )
                )

        return entries
