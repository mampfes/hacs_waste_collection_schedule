import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://webapp-ambiente.gruppohera.it/rifiutologo/rifiutologoweb"


def _pick_town(response, *, town, **_):
    towns = response.json()
    for entry in towns:
        if entry.get("name").upper() == str(town).upper():
            return entry.get("id", "")
    raise SourceArgumentNotFoundWithSuggestions(
        "town", town, [entry.get("name") for entry in towns]
    )


def _pick_street(response, town_id, *, street, **_):
    streets = response.json()
    for entry in streets:
        if entry.get("indirizzo") == str(street).upper():
            return entry.get("id", "")
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, [entry.get("indirizzo") for entry in streets]
    )


def _pick_number(response, town_id, street_id, *, house_number, **_):
    numbers = response.json()
    for entry in numbers:
        if entry.get("numeroCivico") == str(house_number):
            return entry.get("id", "")
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", house_number, [entry.get("numeroCivico") for entry in numbers]
    )


@final
class Source(BaseSource):
    TITLE = "Il Rifiutologo"
    DESCRIPTION = "Source for ilrifiutologo.it"
    URL = "https://ilrifiutologo.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"town": "Faenza", "street": "VIA AUGUSTO RIGHI", "house_number": "6"},
        "Test2": {"town": "Faenza", "street": "VIA AUGUSTO RIGHI", "house_number": 1},
    }

    PARAMS = (city("town"), street("street"), house_number("house_number"))

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(f"{_API}/getComuni.php", pick=_pick_town),
            retrievers.Lookup(
                f"{_API}/getIndirizzi.php",
                params=lambda town_id, **_: {"idComune": town_id},
                pick=_pick_street,
            ),
            retrievers.Lookup(
                f"{_API}/getNumeriCivici.php",
                params=lambda town_id, street_id, **_: {
                    "idComune": town_id,
                    "idIndirizzo": street_id,
                },
                pick=_pick_number,
            ),
        ),
        url=f"{_API}/getCalendarioPap.php",
        params=lambda town_id, street_id, number_id, **_: {
            "idComune": town_id,
            "idIndirizzo": street_id,
            "idCivico": number_id,
            "isBusiness": "0",
            "date": datetime.date.today().strftime("%Y-%m-%dT00:00:00"),
            "giorniDaMostrare": 31,
        },
        raise_for_status=True,
    )
    parse = parsers.JsonParser("calendario")
    # One calendar entry per day, each holding that day's collections.
    preprocess = preprocessors.ExplodeList("conferimenti", into="conferimento")
    transform = JsonTransformer(
        date_key="data",
        type_key=lambda record: record["conferimento"]["macroprodotto"]["descrizione"],
        type_value_map={
            "Indifferenziato": wt.GENERAL_WASTE,
            "Plastica": wt.RECYCLABLES,
            "Lattine": wt.RECYCLABLES,
            "Vetro": wt.GLASS,
            "Organico": wt.ORGANIC,
            "Sfalci e potature": wt.GARDEN_WASTE,
            "Carta e cartone": wt.PAPER,
            "Pannolini/Pannoloni": wt.OTHER,
        },
        carry_raw_label=True,
    )
