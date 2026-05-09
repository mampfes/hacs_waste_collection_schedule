from datetime import datetime, timezone

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "MRC Matawinie (QC)"
DESCRIPTION = "Source script for gmrmatawinie.org"
URL = "https://gmrmatawinie.org"
COUNTRY = "ca"
API_URL = "https://gmrmatawinie.org/wp-content/plugins/mrcmatawinie-gmr/json/collectes_public_cal.json.php"
TEST_CASES = {
    "Saint-Alphonse-Rodriguez": {"city_id": "Saint-Alphonse-Rodriguez"},
    "Saint-Come": {"city_id": "Saint-Côme"},
    "Saint-Damien Secteur Les Cedres du Liban": {
        "city_id": "Saint-Damien - Secteur Les Cèdres du Liban"
    },
}
ICON_MAP = {
    "bac_bleu": "mdi:recycle",
    "bac_brun": "mdi:compost",
    "bac_noir": "mdi:trash-can",
    "encombrants": "mdi:sofa",
}
TYPE_MAP = {
    "bac_bleu": "Recycling",
    "bac_brun": "Organics",
    "bac_noir": "Garbage",
    "encombrants": "Bulky Items",
}
CITIES = {
    "Sainte-Émélie-de-l'Énergie": 989,
    "Saint-Zénon": 990,
    "Saint-Côme": 991,
    "Saint-Alphonse-Rodriguez": 993,
    "Saint-Damien": 994,
    "Saint-Jean-de-Matha": 996,
    "Saint-Félix-de-Valois": 997,
    "Sainte-Béatrix": 998,
    "Sainte-Marcelline-de-Kildare": 1292,
    "Saint-Côme - Secteur Lac Côme": 1596,
    "Saint-Jean-de-Matha - Secteurs rangs St-François et Sacré-Coeur, St-Guillaume, lac Mondor, Pointe du lac Noir": 1605,
    "Saint-Alphonse-Rodriguez - Secteurs lac des Français et lac Cloutier": 1611,
    "Sainte-Béatrix - Secteurs de la Montagne (Montée St-Jacques, rue du Moulin et rue Panoramique) et Petit Beloeil": 1612,
    "Sainte-Émélie-de-l'Énergie - Secteurs Lac Noir et Crique à David": 1613,
    "Saint-Jean-de-Matha - Secteur Chemin du Golf": 1614,
    "Saint-Damien - Secteur Chemin de la Montagne": 1618,
    "Saint-Damien - Secteur Les Cèdres du Liban": 1641,
}

CONFIG_FLOW_TYPES = {
    "city_id": {
        "type": "SELECT",
        "values": list(CITIES.keys()),
        "multiple": False,
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Find your sector on the <a href="https://gmrmatawinie.org/calendriers-collectes/" target="_blank">MRC Matawinie collection calendar</a>.',
    "fr": 'Trouvez votre secteur sur la <a href="https://gmrmatawinie.org/calendriers-collectes/" target="_blank">carte des collectes de la MRC Matawinie</a>.',
}

PARAM_DESCRIPTIONS = {
    "en": {"city_id": "Select your sector from the list"},
    "fr": {"city_id": "Sélectionnez votre secteur dans la liste"},
}

PARAM_TRANSLATIONS = {
    "en": {"city_id": "Sector"},
    "fr": {"city_id": "Secteur"},
}


class Source:
    def __init__(self, city_id: str):
        if city_id not in CITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "city_id",
                city_id,
                list(CITIES.keys()),
            )
        self._sector_id = CITIES[city_id]

    def fetch(self) -> list[Collection]:
        now = datetime.now(timezone.utc)
        from_ts = int(datetime(now.year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        to_ts = int(
            datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp()
            * 1000
        )

        params = {
            "id": self._sector_id,
            "from": from_ts,
            "to": to_ts,
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if not data.get("success") or not data.get("result"):
            raise Exception(f"Failed to get collection schedule for {self._sector_id}")

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
