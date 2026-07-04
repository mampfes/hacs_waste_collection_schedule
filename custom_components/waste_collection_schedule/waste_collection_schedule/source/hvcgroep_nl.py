import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = None
DESCRIPTION = "Source for the Dutch HVCGroep waste management."
URL = "https://www.hvcgroep.nl"


def EXTRA_INFO():
    return [
        {
            "title": s["title"],
            "url": get_main_url(s["api_url"]),
            "default_params": {"service": extract_service_name(s["api_url"])},
        }
        for s in SERVICE_MAP
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
    "Sliedrecht": {
        "postal_code": "3361AK",
        "house_number": "397",
        "service": "sliedrecht",
    },
    "Tollebeek": {"postal_code": "8309AV", "house_number": "1"},
    "Hvcgroep: Tollebeek": {
        "postal_code": "8309AV",
        "house_number": "1",
        "service": "hvcgroep",
    },
    "Reinis": {"postal_code": "3201AA", "house_number": "1", "service": "reinis"},
    "ZRD": {"postal_code": "4691DH", "house_number": "4", "service": "zrd"},
    "Hoorn": {"postal_code": "1628XA", "house_number": "1", "service": "hvcgroep"},
    "Uitgeest": {
        "postal_code": "1911LB",
        "house_number": "14",
    },
}

_LOGGER = logging.getLogger(__name__)

SERVICE_MAP = [
    {
        "title": "Alpen an den Rijn",
        "api_url": "https://afvalkalender.alphenaandenrijn.nl",
        "icons": {
            "pmd-logo-plastic-blik-drank": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "container-ondergronds-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Cranendonck",
        "api_url": "https://afvalkalender.cranendonck.nl",
        "icons": {
            "zak-geel-blik-drank": Icons.RECYCLING,
            "gft": Icons.ORGANIC,
            "doos-karton-papier-avond": Icons.PAPER,
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Cyclus NV",
        "api_url": "https://cyclusnv.nl",
        "icons": {
            "petfles-blik-drankpak_pmd": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "zak-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Dar",
        "api_url": "https://afvalkalender.dar.nl",
        "icons": {
            "dar-rest": Icons.GENERAL_WASTE,
            "dar-gft": Icons.ORGANIC,
            "dar-plastic-plus": Icons.RECYCLING,
            "dar-papier-avond": Icons.PAPER,
            "dar-papier-overdag": Icons.PAPER,
        },
    },
    {
        "title": "Den Haag",
        "api_url": "https://huisvuilkalender.denhaag.nl",
        "icons": {
            "petfles-blik-drankpak_pmd": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "zak-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "GAD",
        "api_url": "https://inzamelkalender.gad.nl",
        "icons": {
            "petfles-blik-drankpak-pmd": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Berkelland",
        "api_url": "https://afvalkalender.gemeenteberkelland.nl",
        "icons": {
            "doos-karton-papier-MEX": Icons.PAPER,
            "doos-karton-papier-EUP": Icons.PAPER,
            "blik-metaal-melkpak-drankpak-zak-oranje-plastic": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "HVC Groep",
        "api_url": "https://inzamelkalender.hvcgroep.nl",
        "icons": {
            "plastic-blik-drinkpak": Icons.RECYCLING,
            "gft": Icons.ORGANIC,
            "papier-en-karton": Icons.PAPER,
            "restafval": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Lingewaard",
        "api_url": "https://afvalwijzer.lingewaard.nl",
        "icons": {
            "plastic-pak-blik": Icons.RECYCLING,
            "papier": Icons.PAPER,
            "bladeren-appel-gft": Icons.ORGANIC,
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Middelburg + Vlissingen",
        "api_url": "https://afvalwijzer.middelburgvlissingen.nl",
        "icons": {
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
            "kliko-groen-gft": Icons.ORGANIC,
            "kliko-grijs-oranje-pmd": Icons.RECYCLING,
            "doos-karton-papier": Icons.PAPER,
        },
    },
    {
        "title": "Gemeente Peel en Maas",
        "api_url": "https://afvalkalender.peelenmaas.nl",
        "icons": {
            "gpem-pmd": Icons.RECYCLING,
            "gpem-rest": Icons.GENERAL_WASTE,
            "gpem-gft": Icons.ORGANIC,
            "gpem-papier": Icons.PAPER,
        },
    },
    {
        "title": "PreZero",
        "api_url": "https://inzamelwijzer.prezero.nl",
        "icons": {
            "suez-pbd": Icons.RECYCLING,
            "suez-papier-en-karton": Icons.PAPER,
            "suez-container": Icons.GENERAL_WASTE,
            "suez-gft": Icons.ORGANIC,
        },
    },
    {
        "title": "Purmerend",
        "api_url": "https://afvalkalender.purmerend.nl",
        "icons": {
            "blik-metaal-melkpak-drankpak-zak-oranje-plastic": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "zak-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Schouwen-Duiveland",
        "api_url": "https://afvalkalender.schouwen-duiveland.nl",
        "icons": {
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "doos-karton-blik-fles-glas-plastic-hero-logo": Icons.RECYCLING,
        },
    },
    {
        "title": "Gemeente Sliedrecht",
        "api_url": "https://afvalkalender.sliedrecht.nl",
        "icons": {
            "plastic-blik-drinkpak": Icons.RECYCLING,
            "gft": Icons.ORGANIC,
            "papier-en-karton": Icons.PAPER,
            "restafval": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Spaarnelanden",
        "api_url": "https://afvalwijzer.spaarnelanden.nl",
        "icons": {
            "restafval": Icons.GENERAL_WASTE,
            "gft": Icons.ORGANIC,
            "papier": Icons.PAPER,
            "pmd": Icons.RECYCLING,
        },
    },
    {
        "title": "Gemeente Sudwest-Fryslan",
        "api_url": "https://afvalkalender.sudwestfryslan.nl",
        "icons": {
            "plastic-tas-hemd": Icons.RECYCLING,
            "appel-gft": Icons.ORGANIC,
            "doos-karton-papier": Icons.PAPER,
            "zak-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Venray",
        "api_url": "https://afvalkalender.venray.nl",
        "icons": {
            "kliko-grijs-rest": Icons.GENERAL_WASTE,
            "kliko-groen-gft": Icons.ORGANIC,
            "zak-geel-blik-drank": Icons.RECYCLING,
            "doos-karton-papier": Icons.PAPER,
        },
    },
    {
        "title": "Gemeente Voorschoten",
        "api_url": "https://afvalkalender.voorschoten.nl",
        "icons": {
            "plastic-pak-blik": Icons.RECYCLING,
            "doos-karton-papier": Icons.PAPER,
            "appel-gft": Icons.ORGANIC,
            "zakken-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Gemeente Waalre",
        "api_url": "https://afvalkalender.waalre.nl",
        "icons": {
            "gft": Icons.ORGANIC,
            "plastic_blik_drank": Icons.RECYCLING,
            "papier": Icons.PAPER,
            "rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Mijn Afval Zaken - BUCH",
        "api_url": "https://www.mijnafvalzaken.nl",
        "icons": {
            "plastic-blik-drinkpak": Icons.RECYCLING,
            "gft": Icons.ORGANIC,
            "papier-en-karton": Icons.PAPER,
            "restafval": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "Reinis",
        "api_url": "https://reinis.nl",
        "icons": {
            "appel-gft": Icons.ORGANIC,
            "plastic-pak-blik": Icons.RECYCLING,
            "doos-karton-papier": Icons.PAPER,
            "kliko-grijs-zak-grijs-rest": Icons.GENERAL_WASTE,
        },
    },
    {
        "title": "ZRD",
        "api_url": "https://www.zrd.nl",
        "icons": {
            "appel en blad": Icons.ORGANIC,  # GFT-afval
            "pet pak blik": Icons.RECYCLING,  # PMD
            "zak rest rest": Icons.GENERAL_WASTE,  # Restafval
            "karton": Icons.PAPER,  # Papier en karton
        },
    },
]


def extract_service_name(api_url):
    name = api_url.split(".")[-2]
    name = name.split("/")[-1]
    return name


def get_service_name_map():
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
        self.house_letter = house_letter
        self.suffix = suffix
        self._url, self._icons = get_service_name_map()[service]

    def fetch(self):
        # Retrieve bagid (unique waste management identifier)
        r = requests.get(f"{self._url}/adressen/{self.postal_code}:{self.house_number}")
        r.raise_for_status()
        data = r.json()

        # Something must be wrong, maybe the address isn't valid? No need to do the extra requests so just return here.
        if len(data) == 0:
            raise SourceArgumentNotFound("postal_code", self.postal_code)

        bag_id = data[0]["bagid"]
        if len(data) > 1 and (self.house_letter or self.suffix):
            _LOGGER.info(f"Checking {self.house_letter} {self.suffix}")
            for address in data:
                if (
                    address["huisletter"].lower() == self.house_letter.lower()
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
