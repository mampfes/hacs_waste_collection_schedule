import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = None
DESCRIPTION = "Source for the Dutch HVCGroep waste management."
URL = "https://www.hvcgroep.nl"


def EXTRA_INFO():
    return [
        {"title": s["title"], "url": get_main_url(s["api_url"])} for s in SERVICE_MAP
    ]


TEST_CASES = {
    "Tollebeek": {"postal_code": "8309AV", "house_number": "1"},
    "Hvgroep: Tollebeek": {
        "postal_code": "8309AV",
        "house_number": "1",
        "service": "hvcgroep",
    },
    "Cyclus": {"postal_code": "2841ML", "house_number": "1090", "service": "cyclusnv"},
    "Mijnblink": {
        "postal_code": "5741BV",
        "house_number": "76",
        "service": "mijnblink",
    },
}

_LOGGER = logging.getLogger(__name__)

SERVICE_MAP = [
    {
        "title": "Alpen an den Rijn",
        "api_url": "https://afvalkalender.alphenaandenrijn.nl",
    },
    {
        "title": "Gemeente Cranendonck",
        "api_url": "https://afvalkalender.cranendonck.nl",
    },
    {
        "title": "Cyclus NV",
        "api_url": "https://afvalkalender.cyclusnv.nl",
    },
    {
        "title": "Dar",
        "api_url": "https://afvalkalender.dar.nl",
    },
    {
        "title": "Den Haag",
        "api_url": "https://huisvuilkalender.denhaag.nl",
    },
    {
        "title": "GAD",
        "api_url": "https://inzamelkalender.gad.nl",
    },
    {
        "title": "Gemeente Berkelland",
        "api_url": "https://afvalkalender.gemeenteberkelland.nl",
    },
    {
        "title": "HVC Groep",
        "api_url": "https://inzamelkalender.hvcgroep.nl",
    },
    {
        "title": "Gemeente Lingewaard",
        "api_url": "https://afvalwijzer.lingewaard.nl",
    },
    {
        "title": "Gemeente Middelburg + Vlissingen",
        "api_url": "https://afvalwijzer.middelburgvlissingen.nl",
    },
    {
        "title": "Mijn Blink",
        "api_url": "https://mijnblink.nl",
    },
    {
        "title": "Gemeente Peel en Maas",
        "api_url": "https://afvalkalender.peelenmaas.nl",
    },
    {
        "title": "PreZero",
        "api_url": "https://inzamelwijzer.prezero.nl",
    },
    {
        "title": "Purmerend",
        "api_url": "https://afvalkalender.purmerend.nl",
    },
    {
        "title": "Reinigingsbedrijf Midden Nederland",
        "api_url": "https://inzamelschema.rmn.nl",
    },
    {
        "title": "Gemeente Schouwen-Duiveland",
        "api_url": "https://afvalkalender.schouwen-duiveland.nl",
    },
    {
        "title": "Spaarne Landen",
        "api_url": "https://afvalwijzer.spaarnelanden.nl",
    },
    {
        "title": "Stadswerk 072",
        "api_url": "https://www.stadswerk072.nl",
    },
    {
        "title": "Gemeente Sudwest-Fryslan",
        "api_url": "https://afvalkalender.sudwestfryslan.nl",
    },
    {
        "title": "Gemeente Venray",
        "api_url": "https://afvalkalender.venray.nl",
    },
    {
        "title": "Gemeente Voorschoten",
        "api_url": "https://afvalkalender.voorschoten.nl",
    },
    {
        "title": "Gemeente Wallre",
        "api_url": "https://afvalkalender.waalre.nl",
    },
    {
        "title": "ZRD",
        "api_url": "https://afvalkalender.zrd.nl",
    },
]


def get_service_name_map():
    def extract_service_name(api_url):
        name = api_url.split(".")[-2]
        name = name.split("/")[-1]
        return name

    return {extract_service_name(s["api_url"]): s["api_url"] for s in SERVICE_MAP}


def get_main_url(url):
    x = url.split(".")[-2:]
    x[0] = x[0].removeprefix("https://")
    return "https://" + ".".join(x)


ICON_MAP = {
    "plastic-blik-drinkpak": "mdi:recycle",
    "gft": "mdi:leaf",
    "papier-en-karton": "mdi:archive",
    "restafval": "mdi:trash-can",
}


class Source:
    def __init__(self, postal_code, house_number, service="hvcgroep"):
        self.postal_code = postal_code
        self.house_number = house_number
        self._url = get_service_name_map()[service]

    def fetch(self):

        # Retrieve bagid (unique waste management identifier)
        r = requests.get(f"{self._url}/adressen/{self.postal_code}:{self.house_number}")
        r.raise_for_status()
        data = r.json()

        # Something must be wrong, maybe the address isn't valid? No need to do the extra requests so just return here.
        if len(data) == 0:
            raise Exception("no data found for this address")

        bag_id = data[0]["bagid"]

        # Retrieve the details about different waste management flows (for example, paper, plastic etc.)
        r = requests.get(f"{self._url}/rest/adressen/{bag_id}/afvalstromen")
        r.raise_for_status()
        waste_flows = r.json()

        # Retrieve the coming pickup dates for waste.
        r = requests.get(f"{self._url}/rest/adressen/{bag_id}/ophaaldata")
        r.raise_for_status()
        data = r.json()

        entries = []

        for item in data:
            waste_details = [
                x for x in waste_flows if x["id"] == item["afvalstroom_id"]
            ]
            entries.append(
                Collection(
                    date=datetime.strptime(item["ophaaldatum"], "%Y-%m-%d").date(),
                    t=waste_details[0]["title"],
                    icon=ICON_MAP.get(waste_details[0]["icon"]),
                )
            )

        return entries
