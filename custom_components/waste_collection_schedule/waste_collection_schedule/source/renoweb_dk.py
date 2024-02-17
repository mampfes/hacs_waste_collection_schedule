""" Support for Renoweb waste collection schedule """

import logging
from typing import List
import re
from datetime import datetime
import json
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]


TITLE = "RenoWeb"
DESCRIPTION = "RenoWeb collections"
URL = "https://renoweb.dk"

TEST_CASES = {
    "test_01": {
        "municipality": "frederiksberg",
        "address": "Roskildevej 40",
    },
    "test_02": {
        "municipality": "htk",
        "address": "🤷",
        "address_id": 45149,
    },
    "test_03": {
        "municipality": "rudersdal",
        "address": "Stationsvej 38",
    }
}

_LOGGER = logging.getLogger('waste_collection_schedule.renoweb_dk')


class Source:
    """ Source class for RenoWeb """

    _api_url: str
    _address_id: int

    def __init__(self, **kwargs):
        _LOGGER.debug("Source.__init__(); %s", kwargs)
        if kwargs and "municipality" in kwargs:
            self._api_url = (
                'https://'
                + kwargs["municipality"].lower()
                + '.renoweb.dk/Legacy/JService.asmx/'
            )

        if kwargs and "address_id" in kwargs:
            self._address_id = kwargs["address_id"]

        if kwargs and "address" in kwargs:
            self._address = kwargs["address"]

    def fetch(self) -> List[Collection]:
        """ Fetch data from RenoWeb """
        _LOGGER.debug("Source.fetch()")

        entries: list[Collection] = []

        session = requests.Session()
        session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
            + "Gecko/20100101 Firefox/115.0",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        if not hasattr(self, '_address_id') and hasattr(self, '_address'):
            response = session.post(
                url=f"{self._api_url}Adresse_SearchByString",
                json={
                    "searchterm": f"{self._address},",
                    "addresswithmateriel": 3
                }
            )

            response.raise_for_status()

            _LOGGER.debug(
                "Address '%s'; id %s",
                json.loads(response.json()['d'])['list'][0]['label'],
                json.loads(response.json()['d'])['list'][0]['value']
            )

            self._address_id = json.loads(response.json()['d'])[
                'list'][0]['value']

        response = session.post(
            url=f"{self._api_url}GetAffaldsplanMateriel_mitAffald",
            json={"adrid": self._address_id, "common": False}
        )

        response.raise_for_status()

        # For some reason the response is a JSON structure inside a JSON string
        for entry in json.loads(response.json()['d'])['list']:

            if (
                not entry['afhentningsbestillingmateriel']
                    and re.search(r'dag den \d{2}-\d{2}-\d{4}', entry['toemningsdato'])
            ):

                response = session.post(
                    url=f"{self._api_url}GetCalender_mitAffald",
                    json={"materialid": entry['id']}
                )

                response.raise_for_status()

                entry['name'] = " - ".join(
                    [entry['ordningnavn'], entry['materielnavn']]
                )

                for date in [
                    datetime.strptime(
                        date_string.split()[-1], "%d-%m-%Y"
                    ).date() for date_string in json.loads(response.json()['d'])['list']
                ]:

                    entries.append(Collection(date=date, t=entry['name']))

        return entries
