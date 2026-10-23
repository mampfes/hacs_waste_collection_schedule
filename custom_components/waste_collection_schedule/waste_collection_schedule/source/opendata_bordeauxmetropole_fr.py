from typing import Any, ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    Compose,
    RequireRecords,
    WeekdayRecurrence,
)
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BAN_URL = "https://api-adresse.data.gouv.fr/search/"
_API_URL = (
    "https://opendata.bordeaux-metropole.fr/api/explore/v2.1/catalog/datasets/"
    "en_frcol_s/records"
)

_INSEE_CODES = {
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


def _point(response, *_, address, city, **__) -> tuple[float, float]:
    """The (lon, lat) the geocoder resolves the address to within the commune."""
    features = response.json().get("features", [])
    if not features:
        raise SourceArgumentNotFound(
            "address", address, f"no address found in {city} for this value."
        )
    lon, lat = features[0]["geometry"]["coordinates"]
    return lon, lat


def _within_point(point: tuple[float, float], **_) -> dict[str, Any]:
    # The dataset's zones are polygons; records without a geometry (geom_err)
    # never intersect, so they are skipped by the server.
    lon, lat = point
    return {
        "where": f"intersects(geo_shape, geom'POINT({lon} {lat})')",
        "select": "type,jour_col",
        "limit": 100,
    }


@final
class Source(BaseSource):
    TITLE = "Bordeaux Métropole"
    DESCRIPTION = "Source script for opendata.bordeaux-metropole.fr"
    URL = "https://opendata.bordeaux-metropole.fr/"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Bordeaux": {"address": "20 Cr Pasteur", "city": "Bordeaux"},
        "Mérignac": {"address": "456 Av. de Verdun", "city": "Mérignac"},
        "Gradignan": {"address": "Avenue de la Libération", "city": "Gradignan"},
        "Talence": {"address": "Cours Gambetta", "city": "Talence"},
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
            "address": "Route de Lacanau",
            "city": "Saint-Aubin-de-Médoc",
        },
        "Saint-Louis-de-Montferrand": {
            "address": "Rue Roget Espagnet",
            "city": "Saint-Louis-de-Montferrand",
        },
        "Saint-Vincent-de-Paul": {
            "address": "Avenue de l'Etang",
            "city": "Saint-Vincent-de-Paul",
        },
    }

    PARAMS = (street_address("address"), dropdown("city", list(_INSEE_CODES)))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your commune and enter your street address without the city "
            "(e.g. '20 Cours Pasteur'). The collection days are those of the "
            "zone the address lies in."
        ),
        "fr": (
            "Choisissez votre commune et saisissez votre adresse sans la "
            "commune (ex : '20 Cours Pasteur'). Les jours de collecte sont "
            "ceux de la zone où se trouve l'adresse."
        ),
    }

    # The dataset publishes zones with a weekday list per stream, not a calendar,
    # so the dates are projected from the next occurrence of each weekday.
    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                _BAN_URL,
                params=lambda address, city, **_: {
                    "q": address,
                    "citycode": _INSEE_CODES[city],
                    "limit": 1,
                },
                pick=_point,
            ),
        ),
        url=_API_URL,
        params=_within_point,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("results")
    preprocess = Compose(
        RequireRecords(argument="address"),
        WeekdayRecurrence(
            day=lambda record: "/".join(record["jour_col"] or []),
            keys=lambda record: record["type"],
        ),
    )
    transform = ICSTransformer(
        type_value_map={"OM": wt.GENERAL_WASTE, "TRI": wt.RECYCLABLES}
    )
