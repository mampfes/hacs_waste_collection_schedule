import json
import urllib.parse
import datetime
from enum import Enum
from typing import Literal


import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Angers Loire Métropole"
DESCRIPTION = "Source script for data.angers.fr"
URL = "https://data.angers.fr/"
TEST_CASES = {
    "TRELAZE": {"address": "cerisiers", "city": "TRELAZE", "typevoie": "ALLEE"},
    "BEAUCOUZE": {"address": "Montreuil", "city": "BEAUCOUZE", "typevoie": "rue"},
    "ANGERS": {"address": "Victor Châtenay", "city": "ANGERS", "typevoie": "AVENUE"},
}

ICON_MAP = {
    "OM": "mdi:trash-can",
    "TRI": "mdi:recycle",
    "enc": "mdi:truck-remove",
    "dv": "mdi:leaf",
    "verre": "mdi:bottle-wine",
}

LABEL_MAP = {
    "OM": "Ordures ménagères",
    "TRI": "Tri sélectif",
}

PARAM_DESCRIPTIONS = {}

# Source : https://data.angers.fr/explore/dataset/secteurs-de-collecte-tri-et-plus/information/
CITY = Literal[
    "LES PONTS DE CE",
    "SAINT BARTHELEMY D ANJOU",
    "SAINT CLEMENT DE LA PLACE",
    "SAINTE GEMMES SUR LOIRE",
    "SAINT LAMBERT LA POTHERIE",
    "SAINT LEGER DE LINIERES",
    "SAINT-LEGER-DES-BOIS",
    "SAINT MARTIN DU FOUILLOUX",
    "LOIRE AUTHION",
    "VERRIERES EN ANJOU",
    "SARRIGNE",
    "SAVENNIERES",
    "SOULAINES SUR AUBANCE",
    "SOULAIRE ET BOURG",
    "TRELAZE",
    "RIVES DU LOIR EN ANJOU",
    "ANGERS",
    "AVRILLE",
    "BEAUCOUZE",
    "BEHUARD",
    "BOUCHEMAINE",
    "BRIOLLAY",
    "CANTENAY EPINARD",
    "ECOUFLANT",
    "ECUILLE",
    "FENEU",
    "LONGUENEE EN ANJOU",
    "MONTREUIL JUIGNE",
    "MURS ERIGNE",
    "PELLOUAILLES LES VIGNES",
    "LE PLESSIS GRAMMOIRE",
]
CITY_NAME = [
    "LES PONTS DE CE",
    "SAINT BARTHELEMY D ANJOU",
    "SAINT CLEMENT DE LA PLACE",
    "SAINTE GEMMES SUR LOIRE",
    "SAINT LAMBERT LA POTHERIE",
    "SAINT LEGER DE LINIERES",
    "SAINT-LEGER-DES-BOIS",
    "SAINT MARTIN DU FOUILLOUX",
    "LOIRE AUTHION",
    "VERRIERES EN ANJOU",
    "SARRIGNE",
    "SAVENNIERES",
    "SOULAINES SUR AUBANCE",
    "SOULAIRE ET BOURG",
    "TRELAZE",
    "RIVES DU LOIR EN ANJOU",
    "ANGERS",
    "AVRILLE",
    "BEAUCOUZE",
    "BEHUARD",
    "BOUCHEMAINE",
    "BRIOLLAY",
    "CANTENAY EPINARD",
    "ECOUFLANT",
    "ECUILLE",
    "FENEU",
    "LONGUENEE EN ANJOU",
    "MONTREUIL JUIGNE",
    "MURS ERIGNE",
    "PELLOUAILLES LES VIGNES",
    "LE PLESSIS GRAMMOIRE",
]

TYPE_VOIE = Literal[
    "LEVEE",
    "RUE",
    "PASSAGE",
    "ROUTE",
    "SQUARE",
    "LIEU DIT",
    "CHEMIN",
    "VENELLE",
    "AVENUE",
    "ZAC",
    "ZA",
    "BOULEVARD",
    "PLACE",
    "ALLEE",
    "IMPASSE",
    "PROMENADE",
    "QUAI",
    "VOIE",
    "SENTIER",
    "COUR",
    "ESPLANADE",
    "MAIL",
    "HAMEAU",
    "AUTOROUTE",
    "CARREFOUR",
    "CLOS",
    "RUELLE",
    "RESIDENCE",
    "MONTEE",
    "ALLEES",
    "CITE",
    "ROND POINT",
    "BOIS",
    "ZI",
    "LOTISSEMENT",
    "PARC",
    "GIRATOIRE",
    "ROCADE",
    "CLOITRE",
    "CALE",
    "ECHANGEUR",
    "RUETTE",
    "AIRE",
    "RAMPE",
    "PORT",
    "ZONE",
    "TRAVERSE",
    "PARVIS",
]
TYPE_VOIE_NAME = [
    "LEVEE",
    "RUE",
    "PASSAGE",
    "ROUTE",
    "SQUARE",
    "LIEU DIT",
    "CHEMIN",
    "VENELLE",
    "AVENUE",
    "ZAC",
    "ZA",
    "BOULEVARD",
    "PLACE",
    "ALLEE",
    "IMPASSE",
    "PROMENADE",
    "QUAI",
    "VOIE",
    "SENTIER",
    "COUR",
    "ESPLANADE",
    "MAIL",
    "HAMEAU",
    "AUTOROUTE",
    "CARREFOUR",
    "CLOS",
    "RUELLE",
    "RESIDENCE",
    "MONTEE",
    "ALLEES",
    "CITE",
    "ROND POINT",
    "BOIS",
    "ZI",
    "LOTISSEMENT",
    "PARC",
    "GIRATOIRE",
    "ROCADE",
    "CLOITRE",
    "CALE",
    "ECHANGEUR",
    "RUETTE",
    "AIRE",
    "RAMPE",
    "PORT",
    "ZONE",
    "TRAVERSE",
    "PARVIS",
]
CONFIG_FLOW_TYPES = {
    "typevoie": {
        "type": "SELECT",
        "values": [f.lower() for f in TYPE_VOIE_NAME],
        "multiple": False,
    },
    "city": {
        "type": "SELECT",
        "values": [f for f in CITY_NAME],
        "multiple": False,
    },
}
EXTRA_INFO = []


class Source:
    api_url_waste_calendar = "https://data.angers.fr/api/explore/v2.1/catalog/datasets/calendrier-tri-et-plus/records?select=date_collecte&where=id_secteur%3D%22{idsecteur}%22&limit=20"
    api_secteur = "https://data.angers.fr/api/explore/v2.1/catalog/datasets/secteurs-de-collecte-tri-et-plus/records?select=id_secteur,cat_secteur&where=typvoie%3D%27{typevoie}%27%20and%20libvoie%20like%20%22*{address}*%22&limit=20&refine=lib_com%3A%22{city}%22"

    def __init__(
        self,
        typevoie: TYPE_VOIE | None = None,
        address: str | None = None,
        city: CITY | None = None,
    ) -> None:
        self.address = address
        self.city = city
        self.typevoie = typevoie

    def _get_idsecteur_address(self, address: str, city: str, typevoie: str) -> dict:
        url = self.api_secteur.format(
            city=urllib.parse.quote(self.city.upper()),
            address=urllib.parse.quote(self.address),
            typevoie=urllib.parse.quote(self.typevoie.upper()),
        )

        response = requests.get(url)

        if response.status_code != 200:
            raise SourceArgumentException(
                "address", "Error response from data.angers.fr id secteur api."
            )

        data = response.json()["results"]

        # Remove duplicates data from the API
        unique_data = [dict(t) for t in {tuple(d.items()) for d in data}]

        if not data:
            raise SourceArgumentException(
                "address", "Pas de données depuis l'api, vérifier l'adresse"
            )

        return unique_data

    def fetch(self) -> list[Collection]:
        try:
            id_secteurs = self._get_idsecteur_address(
                self.address, self.city, self.typevoie
            )
        except requests.RequestException as e:
            raise SourceArgumentException(
                "address", f"Error fetching address data: {e}"
            )

        entries = []
        for id_secteur in id_secteurs:
            try:
                if id_secteur["cat_secteur"] == "OM":
                    url = self.api_url_waste_calendar.format(
                        idsecteur=urllib.parse.quote(id_secteur["id_secteur"])
                    )
                    data_om = requests.get(url)
                    data_om.raise_for_status()
                    dates_om = [
                        entry["date_collecte"] for entry in data_om.json()["results"]
                    ]
                    entries.append({"type": "OM", "results": dates_om})

                elif id_secteur["cat_secteur"] == "TRI":
                    url = self.api_url_waste_calendar.format(
                        idsecteur=urllib.parse.quote(id_secteur["id_secteur"])
                    )
                    data_tri = requests.get(url)
                    data_tri.raise_for_status()
                    dates_tri = [
                        entry["date_collecte"] for entry in data_tri.json()["results"]
                    ]
                    entries.append({"type": "TRI", "results": dates_tri})
                else:
                    raise SourceArgumentException("city", "Error response from API")
            except requests.RequestException as e:
                raise SourceArgumentException(
                    "city", f"Error fetching collection data: {e}"
                )
        final_entries = []
        # print(entries)
        for entry in entries:
            for date_str in entry["results"]:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                final_entries.append(
                    Collection(
                        date=datetime.date(date.year, date.month, date.day),
                        t=LABEL_MAP[entry["type"]],
                        icon=ICON_MAP.get(entry["type"]),
                    )
                )

        return final_entries
