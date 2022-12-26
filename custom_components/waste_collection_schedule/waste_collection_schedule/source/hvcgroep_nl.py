import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "HVCGroep"
DESCRIPTION = "Source for the Dutch HVCGroep waste management."
URL = "https://www.hvcgroep.nl/zelf-regelen/afvalkalender"
TEST_CASES = {
    "Tollebeek": {"postal_code": "8309AV", "house_number": "1"},
    "Hvgroep: Tollebeek": {
        "postal_code": "8309AV",
        "house_number": "1",
        "service": "hvcgroep",
    },
    "Cyclus": {"postal_code": "2841ML", "house_number": "1090", "service": "cyclusnv"},
    "Mjinblink": {
        "postal_code": "5741BV",
        "house_number": "76",
        "service": "mjinblink",
    },
}

_LOGGER = logging.getLogger(__name__)

SERVICE_MAP = {
    "alphenaandenrijn": "https://afvalkalender.alphenaandenrijn.nl",
    "cranendonck": "https://afvalkalender.cranendonck.nl",
    "cyclusnv": "https://afvalkalender.cyclusnv.nl",
    "dar": "https://afvalkalender.dar.nl",
    "denhaag": "https://huisvuilkalender.denhaag.nl",
    "gad": "https://inzamelkalender.gad.nl",
    "gemeenteberkelland": "https://afvalkalender.gemeenteberkelland.nl",
    "hvcgroep": "https://inzamelkalender.hvcgroep.nl",
    "lingewaard": "https://afvalwijzer.lingewaard.nl",
    "middelburgvlissingen": "https://afvalwijzer.middelburgvlissingen.nl",
    "mijnblink": "https://mijnblink.nl",
    "peelenmaas": "https://afvalkalender.peelenmaas.nl",
    "prezero": "https://inzamelwijzer.prezero.nl",
    "purmerend": "https://afvalkalender.purmerend.nl",
    "rmn": "https://inzamelschema.rmn.nl",
    "schouwen-duiveland": "https://afvalkalender.schouwen-duiveland.nl",
    "spaarnelanden": "https://afvalwijzer.spaarnelanden.nl",
    "stadswerk072": "https://www.stadswerk072.nl",
    "sudwestfryslan": "https://afvalkalender.sudwestfryslan.nl",
    "venray": "https://afvalkalender.venray.nl",
    "voorschoten": "https://afvalkalender.voorschoten.nl",
    "waalre": "https://afvalkalender.waalre.nl",
    "zrd": "https://afvalkalender.zrd.nl",
}


class Source:
    def __init__(self, postal_code, house_number, service="hvcgroep"):
        self.postal_code = postal_code
        self.house_number = house_number
        self.icons = {
            "plastic-blik-drinkpak": "mdi:recycle",
            "gft": "mdi:leaf",
            "papier-en-karton": "mdi:archive",
            "restafval": "mdi:trash-can",
        }
        self._url = SERVICE_MAP[service]

    def fetch(self):

        # Retrieve bagid (unique waste management identifier)
        r = requests.get(f"{self._url}/adressen/{self.postal_code}:{self.house_number}")
        r.raise_for_status()
        data = r.json()

        # Something must be wrong, maybe the address isn't valid? No need to do the extra requests so just return here.
        if len(data) == 0:
            _LOGGER.error("no data found for this address")
            return []

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
                    icon=self.icons.get(waste_details[0]["icon"], "mdi:trash-can"),
                )
            )

        return entries
