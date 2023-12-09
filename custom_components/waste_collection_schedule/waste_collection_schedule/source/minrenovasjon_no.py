import datetime
import json
import re
from urllib.parse import urlencode

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Min Renovasjon"
DESCRIPTION = "Source for Norkart Komtek MinRenovasjon (Norway)."
URL = "https://www.norkart.no"

# **street_code:** \
# **county_id:** \
# Can be found with this REST-API call.
# ```
# https://ws.geonorge.no/adresser/v1/#/default/get_sok
# https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
# ```
# "street_code" equals to "adressekode" and "county_id" equals to "kommunenummer".

TEST_CASES = {
    "Sandvika Rådhus": {
        "street_name": "Rådhustorget",
        "house_number": 2,
        "street_code": 2469,
        "county_id": 3024,
    }
}

API_URL = (
    "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx?server="
    "https://komteksky.norkart.no/MinRenovasjon.Api/api/"
)
APP_KEY = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"
ICON_MAP = {
    "": "mdi:trash-can",
    "brush": "mdi:trash-can",
    "elektriskogelektronisk": "mdi:chip",
    "farligavfall": "mdi:trash-can",
    "glassogmetallemballasje": "mdi:trash-can",
    "hageavfall": "mdi:leaf",
    "klaerogsko": "mdi:hanger",
    "matavfall": "mdi:trash-can",
    "matrestavfall": "mdi:trash-can",
    "matrestavfallplast": "mdi:trash-can",
    "metall": "mdi:trash-can",
    "papir": "mdi:newspaper-variant-multiple",
    "pappogkartong": "mdi:archive",
    "plastemballasje": "mdi:trash-can",
    "restavfall": "mdi:trash-can",
    "drikkekartong": "mdi:newspaper-variant-multiple",
    "papppapirdrikkekartong": "mdi:newspaper-variant-multiple",
    "trevirke": "mdi:trash-can",
}


class Source:
    def __init__(self, street_name, house_number, street_code, county_id):
        self._street_name = street_name
        self._house_number = house_number
        self._street_code = street_code
        self._county_id = county_id

    def fetch(self):
        headers = {
            "Kommunenr": str(self._county_id),
            "RenovasjonAppKey": APP_KEY,
            "user-agent": "Home-Assitant-waste-col-sched/0.1",
        }
        args = {}

        r = requests.get(API_URL + "fraksjoner", params=args, headers=headers)

        type = {}
        for f in json.loads(r.content):
            # pprint(f)
            icon_name = re.sub(r"^.*?/(\w+)\.\w{3,4}$", "\\1", f["Ikon"])
            icon = ICON_MAP.get(icon_name)
            type[f["Id"]] = {"name": f["Navn"], "image": f["Ikon"], "icon": icon}

        args = {
            "gatenavn": self._street_name,
            "husnr": self._house_number,
            "gatekode": self._street_code,
        }

        url_with_param = API_URL + "tommekalender?" + urlencode(args)
        r = requests.get(url_with_param, headers=headers)
        entries = []
        for f in json.loads(r.content):
            for d in f["Tommedatoer"]:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S").date(),
                        t=type[f["FraksjonId"]]["name"],
                        icon=type[f["FraksjonId"]]["icon"],
                        picture=type[f["FraksjonId"]]["image"],
                    )
                )

        return entries
