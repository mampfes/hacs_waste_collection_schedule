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
    "Gmina Dobra/Grzepnica/Rezydencka": {"regionId": "112",
                                         "formattedId": "32:11:01:2:0774204:42719:32"},
    "Gmina Topólka/Bielki": {"regionId": "40",
                             "formattedId": "02:17:04:3:0880283:00157:1"},
    "Gmina Topólka/Bielki": {"regionId": "40",
                             "formattedId": "04:11:07:2:0870362::1"}
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
        "regionId": "ID of instance owner",
        "formattedId": "Formatted ID of city/street and houseId"
    }
}


def find_bin_name(binId, json):
    for entry in json:
        if entry['id'] == binId:
            return entry['name']
    raise Exception


schedule_url_template = Template(
    "https://gateway.sisms.pl/akun/api/owners/${regionId}/timetable/get?\
unitId=${formattedId}")


bins_url_template = Template(
    "https://gateway.sisms.pl/akun/api/owners/${regionId}/bins/list?\
unitId=${formattedId}")

_LOGGER = logging.getLogger(__name__)


class Source:
    # argX correspond to the args dict in the source configuration
    def __init__(self, regionId: str, formattedId: str):
        self._schedule_url = schedule_url_template.safe_substitute(
            regionId=regionId, formattedId=formattedId)
        self._bins_url = bins_url_template.safe_substitute(
            regionId=regionId, formattedId=formattedId)

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
