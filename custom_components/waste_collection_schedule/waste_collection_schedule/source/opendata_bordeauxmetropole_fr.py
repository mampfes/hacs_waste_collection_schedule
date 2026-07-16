import json
import urllib.parse
from datetime import date, datetime, timedelta
from enum import Enum
from typing import ClassVar

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Bordeaux Métropole"
DESCRIPTION = "Source script for opendata.bordeaux-metropole.fr"
URL = "https://opendata.bordeaux-metropole.fr/"
TEST_CASES = {
    "Bordeaux": {"address": "20 Cr Pasteur", "city": "Bordeaux"},
    "Mérignac": {"address": "456 Av. de Verdun", "city": "Mérignac"},
    "Gradignan": {"address": "Avenue de la Libération", "city": "Gradignan"},
    "Talence": {"address": "Place de l'Église", "city": "Talence"},
    "Saint-Médard-en-Jalles": {
        "address": "Rue François Mitterrand",
        "city": "Saint-Médard-en-Jalles",
    },
    "Villenave-d'Ornon": {
        "address": "Avenue du Maréchal Leclerc",
        "city": "Villenave-d'Ornon",
    },
    "Bruges": {"address": "Rue de la République", "city": "Bruges"},
    "Bègles": {"address": "Rue Pierre et Marie Curie", "city": "Bègles"},
    "Le Bouscat": {"address": "Avenue de la Libération", "city": "Le Bouscat"},
    "Pessac": {"address": "Avenue Jean Jaurès", "city": "Pessac"},
    "Ambarès-et-Lagrave": {
        "address": "Pl. du 19 Mars 1962",
        "city": "Ambarès-et-Lagrave",
    },
    "Ambès": {"address": "Rue de la Mairie", "city": "Ambès"},
    "Blanquefort": {"address": "Rue de la République", "city": "Blanquefort"},
    "Eysines": {"address": "Avenue de la Libération", "city": "Eysines"},
    "Le Haillan": {"address": "Rue de la République", "city": "Le Haillan"},
    "Le Taillan-Médoc": {
        "address": "Avenue de la Libération",
        "city": "Le Taillan-Médoc",
    },
    "Martignas-sur-Jalle": {
        "address": "Rue de la République",
        "city": "Martignas-sur-Jalle",
    },
    "Parempuyre": {"address": "Rue de la République", "city": "Parempuyre"},
    "Saint-Aubin-de-Médoc": {
        "address": "Rue de la République",
        "city": "Saint-Aubin-de-Médoc",
    },
    "Saint-Louis-de-Montferrand": {
        "address": "Rue Roget Espagnet",
        "city": "Saint-Louis-de-Montferrand",
    },
    "Saint-Vincent-de-Paul": {
        "address": "Rue de la Résistance",
        "city": "Saint-Vincent-de-Paul",
    },
}

ICON_MAP = {
    "omr": Icons.GENERAL_WASTE,
    "emb": Icons.RECYCLING,
    "enc": Icons.BULKY,
    "dv": Icons.ORGANIC,
    "verre": Icons.GLASS,
}

LABEL_MAP = {
    "OM": "Ordures ménagères",
    "TRI": "Tri sélectif",
}

PARAM_DESCRIPTIONS = {
    "fr": {"address": "Votre adresse complète", "city": "Votre ville"},
    "en": {"address": "Your full address", "city": "Your city"},
    "de": {"address": "Ihre vollständige Adresse", "city": "Ihre Stadt"},
    "it": {"address": "Il tuo indirizzo completo", "city": "La tua città"},
}

PARAM_TRANSLATIONS = {
    "fr": {"address": "Adresse", "city": "Ville"},
    "en": {"address": "Address", "city": "City"},
    "de": {"address": "Adresse", "city": "Stadt"},
    "it": {"address": "Indirizzo", "city": "Città"},
}

EXTRA_INFO = [
    {
        "title": "Bordeaux",
        "default_params": {"city": "Bordeaux"},
    },
    {
        "title": "Mérignac",
        "default_params": {"city": "Mérignac"},
    },
    {
        "title": "Gradignan",
        "default_params": {"city": "Gradignan"},
    },
    {
        "title": "Talence",
        "default_params": {"city": "Talence"},
    },
    {
        "title": "Saint-Médard-en-Jalles",
        "default_params": {"city": "Saint-Médard-en-Jalles"},
    },
    {
        "title": "Villenave-d'Ornon",
        "default_params": {"city": "Villenave-d'Ornon"},
    },
    {
        "title": "Bruges",
        "default_params": {"city": "Bruges"},
    },
    {
        "title": "Bègles",
        "default_params": {"city": "Bègles"},
    },
    {
        "title": "Le Bouscat",
        "default_params": {"city": "Le Bouscat"},
    },
    {
        "title": "Pessac",
        "default_params": {"city": "Pessac"},
    },
    {
        "title": "Ambarès-et-Lagrave",
        "default_params": {"city": "Ambarès-et-Lagrave"},
    },
    {
        "title": "Ambès",
        "default_params": {"city": "Ambès"},
    },
    {
        "title": "Blanquefort",
        "default_params": {"city": "Blanquefort"},
    },
    {
        "title": "Eysines",
        "default_params": {"city": "Eysines"},
    },
    {
        "title": "Le Haillan",
        "default_params": {"city": "Le Haillan"},
    },
    {
        "title": "Le Taillan-Médoc",
        "default_params": {"city": "Le Taillan-Médoc"},
    },
    {
        "title": "Martignas-sur-Jalle",
        "default_params": {"city": "Martignas-sur-Jalle"},
    },
    {
        "title": "Parempuyre",
        "default_params": {"city": "Parempuyre"},
    },
    {
        "title": "Saint-Aubin-de-Médoc",
        "default_params": {"city": "Saint-Aubin-de-Médoc"},
    },
    {
        "title": "Saint-Louis-de-Montferrand",
        "default_params": {"city": "Saint-Louis-de-Montferrand"},
    },
    {
        "title": "Saint-Vincent-de-Paul",
        "default_params": {"city": "Saint-Vincent-de-Paul"},
    },
]


class DayNames(Enum):
    MONDAY = "LUNDI"
    TUESDAY = "MARDI"
    WEDNESDAY = "MERCREDI"
    THURSDAY = "JEUDI"
    FRIDAY = "VENDREDI"
    SATURDAY = "SAMEDI"
    SUNDAY = "DIMANCHE"


DAY_NAME_MAP = {
    DayNames.MONDAY: 0,
    DayNames.TUESDAY: 1,
    DayNames.WEDNESDAY: 2,
    DayNames.THURSDAY: 3,
    DayNames.FRIDAY: 4,
    DayNames.SATURDAY: 5,
    DayNames.SUNDAY: 6,
}


class Source:
    geocoder_url = "https://api.publidata.io/v2/geocoder"
    api_url = "https://opendata.bordeaux-metropole.fr/api/explore/v2.1/catalog/datasets/en_frcol_s/exports/json?lang=fr&refine=commune%3A%22{city}%22&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"

    INSEE_CODES: ClassVar = {
        "Bordeaux": 33063,
        "Mérignac": 33281,
        "Gradignan": 33192,
        "Talence": 33522,
        "Saint-Médard-en-Jalles": 33449,
        "Villenave-d'Ornon": 33550,
        "Bruges": 33075,
        "Bègles": 33039,
        "Le Bouscat": 33069,
        "Pessac": 33318,
        "Ambarès-et-Lagrave": 33003,
        "Ambès": 33004,
        "Blanquefort": 33056,
        "Eysines": 33162,
        "Le Haillan": 33200,
        "Le Taillan-Médoc": 33519,
        "Martignas-sur-Jalle": 33273,
        "Parempuyre": 33312,
        "Saint-Aubin-de-Médoc": 33376,
        "Saint-Louis-de-Montferrand": 33434,
        "Saint-Vincent-de-Paul": 33487,
    }

    def __init__(self, address: str, city: str) -> None:
        self.address = address
        self.city = city

    @staticmethod
    def _get_next_weekday(source_date: date, target_day_name: DayNames) -> date:
        source_date_weekday = source_date.weekday()
        target_weekday = DAY_NAME_MAP[target_day_name]
        days_until_target = (target_weekday - source_date_weekday + 7) % 7
        if days_until_target == 0:
            return source_date
        next_target_date = source_date + timedelta(days=days_until_target)
        return next_target_date

    def _get_address_params(self, address: str) -> dict:
        params: dict[str, str | int] = {
            "q": address,
            "citycode": self.INSEE_CODES[self.city],
            "limit": 10,
            "lookup": "publidata",
        }
        response = requests.get(self.geocoder_url, params=params)

        if response.status_code != 200:
            raise SourceArgumentException("address", "Error response from geocoder")

        data = response.json()[0]["data"]["features"]
        if not data:
            raise SourceArgumentException(
                "address", "No results found for the given address and INSEE code"
            )

        lon, lat = data[0]["geometry"]["coordinates"]
        return {
            "lat": lat,
            "lon": lon,
            "address_id": data[0]["properties"]["id"],
        }

    def _is_within_geo_shape(self, geo_shape: dict, address_params: dict) -> bool:
        point_lon, point_lat = address_params["lon"], address_params["lat"]
        polygon = geo_shape["geometry"]["coordinates"][0]
        _type = geo_shape["geometry"]["type"]

        def is_point_in_polygon(point, polygon) -> bool:
            x, y = point
            n = len(polygon)
            inside = False
            p1x, p1y = polygon[0]
            for i in range(n + 1):
                p2x, p2y = polygon[i % n]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y
            return inside

        if _type == "Polygon":
            return is_point_in_polygon((point_lon, point_lat), polygon)
        if _type == "MultiPolygon":
            for poly in polygon:
                if is_point_in_polygon((point_lon, point_lat), poly):
                    return True
        return False

    def fetch(self) -> list[Collection]:
        address_params = self._get_address_params(self.address)

        url = self.api_url.format(city=urllib.parse.quote(self.city))
        response = requests.get(url)

        if response.status_code != 200:
            raise SourceArgumentException("city", "Error response from API")

        # Records without a geo_shape have a broken geometry (geom_err) in the upstream
        # dataset — they are not city-wide zones. Skip them to avoid spurious matches.
        list_of_infos = [
            i
            for i in json.loads(response.text)
            if i["geo_shape"]
            and self._is_within_geo_shape(i["geo_shape"], address_params)
        ]

        filtered_responses: dict[str, list[str]] = {}
        for response_item in list_of_infos:
            waste_collection_per_type = filtered_responses.setdefault(
                response_item["type"], []
            )
            for jour_col in response_item["jour_col"]:
                waste_collection_per_type.append(jour_col)

        entries = []
        for _collection_type, _dates in filtered_responses.items():
            for _day in _dates:
                source_date = datetime.today().date()
                for _ in range(4):
                    next_date = self._get_next_weekday(source_date, DayNames(_day))
                    entries.append(
                        Collection(
                            date=next_date,
                            t=LABEL_MAP.get(_collection_type, _collection_type),
                            icon=ICON_MAP.get(_collection_type),
                        )
                    )
                    source_date = next_date + timedelta(days=1)

        return entries
