import datetime
import json
import re
from urllib.parse import urlparse, parse_qsl

import requests
from waste_collection_schedule import Collection

TITLE = "Wrocław"
DESCRIPTION = "Source for ekosystem.wroc.pl for Wrocław, Poland"
URL = "https://ekosystem.wroc.pl"
TEST_CASES = {
    "Legnicka 160": {"location_id": 650358},
    "Marcepanowa 7": {"location_id": 680085},
}

ICON_MAP = {
    "zmieszane": "mdi:trash-can",  # Mixed
    "tworzywa": "mdi:recycle",  # Plastic
    "BIO": "mdi:leaf",  # Organic
    "papier": "mdi:file-outline",  # Paper
    "szkło": "mdi:glass-fragile"  # Glass
}

API_URL = "https://ekosystem.wroc.pl/wp-admin/admin-ajax.php"

MESSAGE_FIELD_NAME = 'wiadomosc'
PARAMS_NUMBER_PARAM_NAME = 'params'
WASTE_TYPE_PARAM_FORMAT = "co_{}"
DATE_PARAM_FORMAT = "kiedy_{}"


class Source:
    def __init__(self, location_id):
        self._location_id = location_id
        self._calendar_url_pattern = re.compile(
            "<a href=\"(https://ekosystem\\.wroc\\.pl/download/\\?action=pdf[^\"]*)\"")

    def fetch(self):

        r = requests.post(API_URL, data=dict(action="waste_disposal_form_get_schedule", id_numeru=self._location_id))
        data = json.loads(r.text)

        calendar_data = self.extract_calendar_data(data)
        entries = []

        if PARAMS_NUMBER_PARAM_NAME not in calendar_data:
            raise Exception(f"Error: parameter number not present in the url!")

        for i in range(1, int(calendar_data[PARAMS_NUMBER_PARAM_NAME]) + 1):
            date_str = calendar_data[DATE_PARAM_FORMAT.format(i)]
            type_str = calendar_data[WASTE_TYPE_PARAM_FORMAT.format(i)]
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(date_str, "%Y-%m-%d").date(),
                    t=type_str.capitalize(),
                    icon=ICON_MAP.get(type_str)
                )
            )

        return entries

    def extract_calendar_data(self, data: dict) -> dict:
        if MESSAGE_FIELD_NAME not in data:
            raise Exception("Error: the message field not found")
        message = data[MESSAGE_FIELD_NAME]
        match = self._calendar_url_pattern.search(message)
        if not match:
            raise Exception(f"Error: a message {message} does not contain a valid calendar url!")
        calendar_url = match.group(1)
        parsed_url = urlparse(calendar_url)
        params_list = parse_qsl(parsed_url.query)
        return {k: v for (k, v) in params_list}
