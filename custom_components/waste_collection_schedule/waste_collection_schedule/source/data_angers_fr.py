from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, integer, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://data.angers.fr/api/explore/v2.1/catalog/datasets"

# Source: https://data.angers.fr/explore/dataset/secteurs-de-collecte-tri-et-plus/information/
_CITIES = [
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

_STREET_TYPES = [
    "levee",
    "rue",
    "passage",
    "route",
    "square",
    "lieu dit",
    "chemin",
    "venelle",
    "avenue",
    "zac",
    "za",
    "boulevard",
    "place",
    "allee",
    "impasse",
    "promenade",
    "quai",
    "voie",
    "sentier",
    "cour",
    "esplanade",
    "mail",
    "hameau",
    "autoroute",
    "carrefour",
    "clos",  # codespell:ignore clos
    "ruelle",
    "residence",
    "montee",
    "allees",
    "cite",
    "rond point",
    "bois",
    "zi",
    "lotissement",
    "parc",
    "giratoire",
    "rocade",
    "cloitre",
    "cale",
    "echangeur",
    "ruette",
    "aire",
    "rampe",
    "port",
    "zone",
    "traverse",
    "parvis",
]


def _in_sector(sector: dict, num_voie: int | None) -> bool:
    """Does the house number fall into the sector's number range and side of the
    street (``icote`` "P" even, "I" odd, anything else both)?"""
    if num_voie is None:
        return True
    first, last = sector["num_debut"], sector["num_fin"]
    if (
        first is not None
        and last is not None
        and not int(first) <= num_voie <= int(last)
    ):
        return False
    if sector["icote"] == "P":
        return num_voie % 2 == 0
    if sector["icote"] == "I":
        return num_voie % 2 == 1
    return True


def _sectors(response, *_, address, num_voie=None, **__) -> list[tuple[str, str]]:
    """The distinct ``(sector id, category)`` pairs serving the address."""
    found = {
        sector["id_secteur"]: sector["cat_secteur"]
        for sector in response.json()["results"]
        if _in_sector(sector, num_voie)
    }
    if not found:
        raise SourceArgumentNotFound("address", address)
    return list(found.items())


@final
class Source(BaseSource):
    TITLE = "Angers Loire Métropole"
    DESCRIPTION = "Source script for data.angers.fr"
    URL = "https://data.angers.fr/"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "TRELAZE": {"address": "cerisiers", "city": "TRELAZE", "typevoie": "allee"},
        "BEAUCOUZE": {"address": "Montreuil", "city": "BEAUCOUZE", "typevoie": "rue"},
        "ANGERS_ODD": {
            "address": "Bouchemaine",
            "city": "ANGERS",
            "typevoie": "route",
            "num_voie": 9,
        },
        "ANGERS_EVEN": {
            "address": "Bouchemaine",
            "city": "ANGERS",
            "typevoie": "route",
            "num_voie": 34,
        },
    }

    PARAMS = (
        dropdown("typevoie", _STREET_TYPES, label="Street type"),
        street(field="address"),
        dropdown("city", _CITIES, label="City"),
        integer("num_voie", label="House number"),
    )

    HOWTO: ClassVar[dict] = {
        "fr": (
            "Choisissez la commune et le type de voie, puis saisissez (une partie "
            "de) le nom de la rue. Le numéro est facultatif mais nécessaire si la "
            "rue est répartie sur plusieurs secteurs de collecte."
        ),
        "en": (
            "Select your city and street type, then enter (part of) the street "
            "name. The house number is optional but needed when the street is "
            "split between several collection sectors."
        ),
    }

    retrieve = FanOutRetriever(
        prepare=Lookup(
            f"{_API}/secteurs-de-collecte-tri-et-plus/records",
            params=lambda address, city, typevoie, **_: {
                "select": "id_secteur,cat_secteur,num_debut,num_fin,icote",
                "where": (
                    f"typvoie='{typevoie.upper()}' and libvoie like \"*{address}*\""
                ),
                "refine": f'lib_com:"{city.upper()}"',
                "limit": 100,
            },
            pick=_sectors,
        ),
        targets=lambda source, sectors: sectors,
        fetch=Request(
            f"{_API}/calendrier-tri-et-plus/records",
            params=lambda sector, _all, **_: {
                "select": f'date_collecte,"{sector[1]}" as kind',
                "where": f'id_secteur="{sector[0]}"',
                "limit": 100,
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser("results"))
    transform = JsonTransformer(
        date_key="date_collecte",
        type_key="kind",
        type_value_map={"OM": wt.GENERAL_WASTE, "TRI": wt.RECYCLABLES},
    )
