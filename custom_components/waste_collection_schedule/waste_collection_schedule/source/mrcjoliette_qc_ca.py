from datetime import datetime, timezone

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "MRC Joliette (QC)"
DESCRIPTION = "Source script for mrcjoliette.qc.ca"
URL = "https://mrcjoliette.qc.ca"
COUNTRY = "ca"
API_URL = "https://mrcjoliette.qc.ca/wp-content/plugins/mrcjoliette-gmr/json/collectes_public_cal.json.php"
TEST_CASES = {
    "Joliette Mardi": {"city_id": "Joliette - Mardi"},
    "Saint-Charles-Borromée Mercredi": {"city_id": "Saint-Charles-Borromée - Mercredi"},
    "Crabtree": {"city_id": "Crabtree"},
}
ICON_MAP = {
    "bac_bleu": "mdi:recycle",
    "bac_brun": "mdi:compost",
    "bac_noir": "mdi:trash-can",
    "encombrants": "mdi:sofa",
    "residus_verts": "mdi:leaf",
}
TYPE_MAP = {
    "bac_bleu": "Recycling",
    "bac_brun": "Organics",
    "bac_noir": "Garbage",
    "encombrants": "Bulky Items",
    "residus_verts": "Yard Waste",
}
CITIES = {
    6042: "Crabtree",
    4246: "Crabtree - Domaine",
    6041: "Joliette - Mardi",
    4252: "Joliette - Mercredi",
    4253: "Joliette - Jeudi",
    6050: "Joliette - Centre-ville",
    6043: "Notre-Dame-de-Lourdes",
    6051: "Notre-Dame-de-Lourdes - Domaine",
    6044: "Notre-Dame-des-Prairies",
    6052: "Notre-Dame-des-Prairies - Domaine",
    6045: "Saint-Ambroise-de-Kildare",
    3963: "Saint-Charles-Borromée - Mercredi",
    6053: "Saint-Charles-Borromée - Jeudi",
    4250: "Saint-Charles-Borromée - Domaine",
    6046: "Sainte-Mélanie",
    6047: "Saint-Paul",
    6048: "Saint-Thomas",
    6049: "Village Saint-Pierre",
}

CONFIG_FLOW_TYPES = {
    "city_id": {
        "type": "SELECT",
        "values": list(CITIES.values()),
        "multiple": False,
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Find your sector ID on the <a href="https://mrcjoliette.qc.ca/gmr/carte-des-collectes/" target="_blank">MRC Joliette collection map</a>.',
    "fr": 'Trouvez l\'ID de votre secteur sur la <a href="https://mrcjoliette.qc.ca/gmr/carte-des-collectes/" target="_blank">carte des collectes de la MRC Joliette</a>.',
}

PARAM_DESCRIPTIONS = {
    "en": {"city_id": "Select your city/sector from the list"},
    "fr": {"city_id": "Sélectionnez votre ville/secteur dans la liste"},
}

PARAM_TRANSLATIONS = {
    "en": {"city_id": "City/Sector"},
    "fr": {"city_id": "Ville/Secteur"},
}


class Source:
    def __init__(self, city_id: str):
        city_id_num = None
        for num, name in CITIES.items():
            if name == city_id:
                city_id_num = num
                break
        if city_id_num is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city_id",
                city_id,
                list(CITIES.values()),
            )
        self._city_id = city_id_num

    def fetch(self) -> list[Collection]:
        now = datetime.now(timezone.utc)
        from_ts = int(datetime(now.year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        to_ts = int(
            datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp()
            * 1000
        )

        params = {
            "id": self._city_id,
            "from": from_ts,
            "to": to_ts,
            "utc_offset_from": 0,
            "utc_offset_to": 0,
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if not data.get("success") or not data.get("result"):
            raise Exception(
                f"Failed to get collection schedule for {CITIES[self._city_id]}"
            )

        entries = []

        for item in data["result"]:
            color = item.get("color")
            start_ms = item.get("start")

            if not color or not start_ms:
                continue

            date = datetime.fromtimestamp(start_ms / 1000).date()
            waste_type = TYPE_MAP.get(color, color)

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(color),
                )
            )

        return entries
