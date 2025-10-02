import requests
import json
import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Oslo Kommune"
DESCRIPTION = "Oslo Kommune (Norway)."
URL = "https://www.oslo.kommune.no"

# **street_id:** \
# Can be found with this REST-API call.
# ```
# https://ws.geonorge.no/adresser/v1/#/default/get_sok
# https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
# ```
# "street_id" equals to "adressekode".

TEST_CASES = {
    "Villa Paradiso": {
        "street_name": "Olaf Ryes Plass",
        "house_number": 8,
        "house_letter": '',
        "street_id": 15331
    },
    "Nåkkves vei": {
        "street_name": "Nåkkves vei",
        "house_number": 5,
        "house_letter": '',
        "street_id": 15280,
        "point_id": 38175
    }
}

API_URL = "https://www.oslo.kommune.no/xmlhttprequest.php"
ICON_MAP = {
    "":           "mdi:trash-can",
    "restavfall": "mdi:trash-can",
    "papir":      "mdi:newspaper-variant-multiple"
}

# ### Arguments affecting the configuration GUI ####

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "point_id": "Optional waste point ID to filter by",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "point_id": "Point ID",
    },
}

# ### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(
        self,
        street_name: str,
        house_number: int,
        street_id: int,
        house_letter: str | None = None,
        point_id: int | None = None,
    ):
        self._street_name = street_name
        self._house_number = house_number
        self._street_id = street_id
        self._house_letter = house_letter
        self._point_id = point_id

    def fetch(self):
        headers = {
            'user-agent': 'Home-Assitant-waste-col-sched/0.1'
        }

        args = {
            'service':   'ren.search',
            'street':    self._street_name,
            'number':    self._house_number,
            'letter':    self._house_letter,
            'street_id': self._street_id,
        }

        if self._house_letter:
            args['letter'] = self._house_letter

        r = requests.get(API_URL, params = args, headers = headers)

        entries = []
        res = json.loads(r.content)['data']['result'][0]['HentePunkts']
        for f in res:
            if self._point_id and int(f['Id']) != int(self._point_id):
                continue

            tjenester = f['Tjenester']
            for tjeneste in tjenester:
                tekst = tjeneste['Fraksjon']['Tekst']
                entries.append(
                    Collection(
                        date = datetime.datetime.strptime(
                            tjeneste['TommeDato'], "%d.%m.%Y"
                        ).date(),
                        t = tekst,
                        icon = ICON_MAP.get(tekst.lower())
                    )
                )

        return entries
