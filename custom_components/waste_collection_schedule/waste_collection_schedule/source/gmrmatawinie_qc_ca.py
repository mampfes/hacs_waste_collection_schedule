from datetime import datetime, timezone
from typing import ClassVar, TypedDict, final
from zoneinfo import ZoneInfo

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://gmrmatawinie.org/wp-content/plugins/mrcmatawinie-gmr/json/collectes_public_cal.json.php"

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

_TYPE_MAP = {
    "bac_bleu": wt.RECYCLABLES,
    "bac_brun": wt.ORGANIC,
    "bac_noir": wt.GENERAL_WASTE,
    "encombrants": wt.BULKY_WASTE,
}


class _Event(TypedDict):
    """The fields the transformer reads from each calendar entry."""

    color: str
    start: int


def _calendar_params(city_id, **_):
    # The API wants the calendar year as a millisecond epoch window, computed
    # fresh each fetch so a long-running instance rolls over the new year.
    if city_id not in CITIES:
        raise SourceArgumentNotFoundWithSuggestions(
            "city_id", city_id, list(CITIES.keys())
        )
    now = datetime.now(timezone.utc)
    start = int(datetime(now.year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(
        datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000
    )
    return {"id": CITIES[city_id], "from": start, "to": end}


@final
class Source(BaseSource):
    TITLE = "MRC Matawinie (QC)"
    DESCRIPTION = "Source script for gmrmatawinie.org"
    URL = "https://gmrmatawinie.org"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Saint-Alphonse-Rodriguez": {"city_id": "Saint-Alphonse-Rodriguez"},
        "Saint-Come": {"city_id": "Saint-Côme"},
        "Saint-Damien Secteur Les Cedres du Liban": {
            "city_id": "Saint-Damien - Secteur Les Cèdres du Liban"
        },
    }

    PARAMS = (dropdown("city_id", list(CITIES), label="Sector"),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your sector on the MRC Matawinie collection calendar at https://gmrmatawinie.org/calendriers-collectes/ and select it from the list.",
        "fr": "Trouvez votre secteur sur la carte des collectes de la MRC Matawinie (https://gmrmatawinie.org/calendriers-collectes/) et sélectionnez-le dans la liste.",
    }

    retrieve = retrievers.HttpGetRetriever(url=API_URL, params=_calendar_params)
    parse = parsers.JsonParser("result", shape=list[_Event])

    transform = JsonTransformer(
        date_key="start",
        type_key="color",
        parse_date=date_parsers.from_epoch(unit="ms", tz=ZoneInfo("America/Toronto")),
        type_value_map=_TYPE_MAP,
    )
