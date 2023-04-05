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
    "Alphen a/d Rijn": {
        "postal_code": "2404EN",
        "house_number": "7",
        "service": "alphenaandenrijn",
    },
    "Cranendonck": {
        "postal_code": "6027PL",
        "house_number": "1",
        "house_letter": "b",
        "service": "cranendonck",
    },
    "Cyclus": {"postal_code": "2841ML", "house_number": "1090", "service": "cyclusnv"},
    "GAD": {"postal_code": "1401EE", "house_number": "22", "service": "gad"},
    "Den Haag": {"postal_code": "2591BB", "house_number": "87", "service": "denhaag"},
    "Peel en Maas": {
        "postal_code": "5991GT",
        "house_number": "1",
        "service": "peelenmaas",
    },
    "Tollebeek": {"postal_code": "8309AV", "house_number": "1"},
    "Hvcgroep: Tollebeek": {
        "postal_code": "8309AV",
        "house_number": "1",
        "service": "hvcgroep",
    },
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
        "icons": {
            "pmd-logo-plastic-blik-drank": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "container-ondergronds-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Cranendonck",
        "api_url": "https://afvalkalender.cranendonck.nl",
        "icons": {
            "zak-geel-blik-drank": "mdi:recycle",
            "gft": "mdi:leaf",
            "doos-karton-papier-avond": "mdi:archive",
            "kliko-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Cyclus NV",
        "api_url": "https://afvalkalender.cyclusnv.nl",
        "icons": {
            "petfles-blik-drankpak_pmd": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "zak-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Dar",
        "api_url": "https://afvalkalender.dar.nl",
        "icons": {
            "dar-rest": "mdi:trash-can",
            "dar-gft": "mdi:leaf",
            "dar-plastic-plus": "mdi:recycle",
            "dar-papier-avond": "mdi:archive",
            "dar-papier-overdag": "mdi:archive",
        },
    },
    {
        "title": "Den Haag",
        "api_url": "https://huisvuilkalender.denhaag.nl",
        "icons": {
            "petfles-blik-drankpak_pmd": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "zak-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "GAD",
        "api_url": "https://inzamelkalender.gad.nl",
        "icons": {
            "petfles-blik-drankpak-pmd": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "kliko-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Berkelland",
        "api_url": "https://afvalkalender.gemeenteberkelland.nl",
        "icons": {
            "doos-karton-papier-MEX": "mdi:archive",
            "doos-karton-papier-EUP": "mdi:archive",
            "blik-metaal-melkpak-drankpak-zak-oranje-plastic": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "kliko-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "HVC Groep",
        "api_url": "https://inzamelkalender.hvcgroep.nl",
        "icons": {
            "plastic-blik-drinkpak": "mdi:recycle",
            "gft": "mdi:leaf",
            "papier-en-karton": "mdi:archive",
            "restafval": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Lingewaard",
        "api_url": "https://afvalwijzer.lingewaard.nl",
        "icons": {
            "plastic-pak-blik": "mdi:recycle",
            "papier": "mdi:archive",
            "bladeren-appel-gft": "mdi:leaf",
            "kliko-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Middelburg + Vlissingen",
        "api_url": "https://afvalwijzer.middelburgvlissingen.nl",
        "icons": {
            "kliko-grijs-rest": "mdi:trash-can",
            "kliko-groen-gft": "mdi:leaf",
            "kliko-grijs-oranje-pmd": "mdi:recycle",
            "doos-karton-papier": "mdi:archive",
        },
    },
    {
        "title": "Mijn Blink",
        "api_url": "https://mijnblink.nl",
        "icons": {
            "zak-grijs-rest": "mdi:trash-can",
            "appel-gft": "mdi:leaf",
            "blik-metaal-melkpak-drankpak-zak-oranje-plastic": "mdi:recycle",
            "doos-karton-papier": "mdi:archive",
        },
    },
    {
        "title": "Gemeente Peel en Maas",
        "api_url": "https://afvalkalender.peelenmaas.nl",
        "icons": {
            "gpem-pmd": "mdi:recycle",
            "gpem-rest": "mdi:trash-can",
            "gpem-gft": "mdi:leaf",
            "gpem-papier": "mdi:archive",
        },
    },
    {
        "title": "PreZero",
        "api_url": "https://inzamelwijzer.prezero.nl",
        "icons": {
            "suez-pbd": "mdi:recycle",
            "suez-papier-en-karton": "mdi:archive",
            "suez-container": "mdi:trash-can",
            "suez-gft": "mdi:leaf",
        },
    },
    {
        "title": "Purmerend",
        "api_url": "https://afvalkalender.purmerend.nl",
        "icons": {
            "blik-metaal-melkpak-drankpak-zak-oranje-plastic": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "zak-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Schouwen-Duiveland",
        "api_url": "https://afvalkalender.schouwen-duiveland.nl",
        "icons": {
            "kliko-grijs-rest": "mdi:trash-can",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "doos-karton-blik-fles-glas-plastic-hero-logo": "mdi:recycle",
        },
    },
    {
        "title": "Spaarnelanden",
        "api_url": "https://afvalwijzer.spaarnelanden.nl",
        "icons": {
            "restafval": "mdi:trash-can",
            "gft": "mdi:leaf",
            "papier": "mdi:archive",
            "pmd": "mdi:recycle",
        },
    },
    {
        "title": "Gemeente Sudwest-Fryslan",
        "api_url": "https://afvalkalender.sudwestfryslan.nl",
        "icons": {
            "plastic-tas-hemd": "mdi:recycle",
            "appel-gft": "mdi:leaf",
            "doos-karton-papier": "mdi:archive",
            "zak-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Venray",
        "api_url": "https://afvalkalender.venray.nl",
        "icons": {
            "kliko-grijs-rest": "mdi:trash-can",
            "kliko-groen-gft": "mdi:leaf",
            "zak-geel-blik-drank": "mdi:recycle",
            "doos-karton-papier": "mdi:archive",
        },
    },
    {
        "title": "Gemeente Voorschoten",
        "api_url": "https://afvalkalender.voorschoten.nl",
        "icons": {
            "plastic-pak-blik": "mdi:recycle",
            "doos-karton-papier": "mdi:archive",
            "appel-gft": "mdi:leaf",
            "zakken-grijs-rest": "mdi:trash-can",
        },
    },
    {
        "title": "Gemeente Waalre",
        "api_url": "https://afvalkalender.waalre.nl",
        "icons": {
            "gft": "mdi:leaf",
            "plastic_blik_drank": "mdi:recycle",
            "papier": "mdi:archive",
            "rest": "mdi:trash-can",
        },
    },
    {
        "title": "ZRD",
        "api_url": "https://afvalkalender.zrd.nl",
        "icons": {
            "blik-metaal-melkpak-drankpak-zak-oranje-plastic": "mdi:recycle",
            "doos-karton-papier": "mdi:archive",
            "appel-gft": "mdi:leaf",
            "kliko-grijs-rest": "mdi:trash-can",
        },
    },
]


def get_service_name_map():
    def extract_service_name(api_url):
        name = api_url.split(".")[-2]
        name = name.split("/")[-1]
        return name

    return {
        extract_service_name(s["api_url"]): (s["api_url"], s["icons"])
        for s in SERVICE_MAP
    }


def get_main_url(url):
    x = url.split(".")[-2:]
    x[0] = x[0].removeprefix("https://")
    return "https://" + ".".join(x)


class Source:
    def __init__(
        self, postal_code, house_number, house_letter="", suffix="", service="hvcgroep"
    ):
        self.postal_code = postal_code
        self.house_number = house_number
        self.house_letter = postal_code
        self.suffix = suffix
        self._url, self._icons = get_service_name_map()[service]

    def fetch(self):

        # Retrieve bagid (unique waste management identifier)
        r = requests.get(f"{self._url}/adressen/{self.postal_code}:{self.house_number}")
        r.raise_for_status()
        data = r.json()

        # Something must be wrong, maybe the address isn't valid? No need to do the extra requests so just return here.
        if len(data) == 0:
            raise Exception("no data found for this address")

        bag_id = data[0]["bagid"]
        if len(data) > 1 and self.house_letter and self.suffix:
            _LOGGER.info(f"Checking {self.house_letter} {self.suffix}")
            for address in data:
                if (
                    address["huisletter"] == self.house_letter
                    and address["toevoeging"] == self.suffix
                ):
                    bag_id = address["bagid"]
                    break

        # Retrieve the details about different waste management flows (for example, paper, plastic etc.)
        r = requests.get(f"{self._url}/rest/adressen/{bag_id}/afvalstromen")
        r.raise_for_status()
        waste_flows = r.json()

        # Retrieve the pickup calendar for waste.
        r = requests.get(
            f"{self._url}/rest/adressen/{bag_id}/kalender/{datetime.today().year}"
        )
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
                    icon=self._icons.get(waste_details[0]["icon"]),
                )
            )

        return entries
