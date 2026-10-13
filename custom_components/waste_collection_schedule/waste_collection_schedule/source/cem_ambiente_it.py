from difflib import get_close_matches
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

API = "https://cemfacile.cemambiente.it/public"

_MUNICIPALITIES = (
    "Agrate Brianza, Aicurzio, Arcore, Basiano, Bellinzago Lombardo, Bellusco, "
    "Bernareggio, Borgo San Giovanni, Brugherio, Burago Di Molgora, Busnago, "
    "Bussero, Cambiago, Camparada, Caponago, Carnate, Carpiano, Carugate, "
    "Casaletto Lodigiano, Casalmaiocco, Caselle Lurani, Cassano D'Adda, "
    "Cassina De' Pecchi, Cavenago Di Brianza, Cernusco Sul Naviglio, "
    "Cerro Al Lambro, Cervignano D'Adda, Cologno Monzese, Colturano, Comazzo, "
    "Concorezzo, Cornate D'Adda, Correzzana, Dresano, Gessate, Gorgonzola, "
    "Grezzago, Inzago, Lesmo, Liscate, Macherio, Masate, Massalengo, Mediglia, "
    "Melegnano, Melzo, Merlino, Mezzago, Mulazzano, Ornago, Pantigliate, Paullo, "
    "Pessano Con Bornago, Pozzo D'Adda, Pozzuolo Martesana, Rodano, Roncello, "
    "Ronco Briantino, Salerano sul Lambro, San Zenone Al Lambro, "
    "Sant'Angelo Lodigiano, Settala, Sordio, Sulbiate, Torrevecchia Pia, "
    "Trezzano Rosa, Trezzo Sull'Adda, Tribiano, Truccazzano, Usmate Velate, "
    "Vaprio D'Adda, Vedano Al Lambro, Vignate, Villasanta, Vimercate, "
    "Vimodrone, Vizzolo Predabissi"
).split(", ")


def _match(rows: list, wanted: str, argument: str) -> dict:
    """The row whose name equals ``wanted`` (case-insensitively), else raise."""
    target = str(wanted).strip().casefold()
    for row in rows:
        if str(row.get("nome", "")).casefold() == target:
            return row
    names = [str(row.get("nome", "")) for row in rows]
    raise SourceArgumentNotFoundWithSuggestions(
        argument,
        wanted,
        get_close_matches(str(wanted), names, n=5, cutoff=0.4) or sorted(names),
    )


def _pick_municipality(response, *keys, city, **_) -> int:
    return _match(response.json().get("body", []), city, "city")["idSiunet"]


def _pick_street(response, *keys, street, **_) -> dict:
    via = _match(response.json().get("body", []), street, "street")
    return {"idVia": via["idVia"], "nomeVia": via["nome"]}


@final
class Source(BaseSource):
    TITLE = "CEM Ambiente"
    DESCRIPTION = (
        "Source for CEM Ambiente (CEM FACILE), covering municipalities in the "
        "Milano / Monza e Brianza / Lodi area of Italy."
    )
    URL = "https://www.cemambiente.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Vimodrone, Via Aldo Moro": {"city": "Vimodrone", "street": "Via Aldo Moro"},
        "Cologno Monzese, Via Cadore": {
            "city": "Cologno Monzese",
            "street": "Via Cadore",
        },
        "Vimercate, Via Cesare Battisti": {
            "city": "Vimercate",
            "street": "Via Cesare Battisti",
        },
    }

    REGIONS = tuple(region(name, city=name) for name in _MUNICIPALITIES)

    PARAMS = (city(), street())

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.PLASTIC,
        wt.GENERAL_WASTE,
        wt.OTHER,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the municipality (comune) and street (via) exactly as they are "
            "known to CEM Ambiente, e.g. as shown on "
            "https://www.cemambiente.it/cemfacile/. If the exact spelling isn't "
            "found, the error message will list the closest matching street names "
            "for your municipality."
        ),
        "it": (
            "Inserisci il comune e la via esattamente come sono indicati da CEM "
            "Ambiente, ad esempio come mostrato su "
            "https://www.cemambiente.it/cemfacile/. Se l'ortografia esatta non "
            "viene trovata, il messaggio di errore elencherà le vie più simili per "
            "il tuo comune."
        ),
    }

    retrieve = retrievers.Request(
        f"{API}/getCalendario",
        method="POST",
        json=lambda id_siunet, via, **_: {"idSiunet": id_siunet, **via},
        before=(
            retrievers.Lookup(
                f"{API}/listComuni", method="POST", json={}, pick=_pick_municipality
            ),
            retrievers.Lookup(
                f"{API}/listVie",
                method="POST",
                json=lambda id_siunet, **_: {"idSiunet": id_siunet},
                pick=_pick_street,
            ),
        ),
    )

    parse = parsers.JsonParser("body")

    transform = JsonTransformer(
        date_key="data",
        # "UMI - Raccolta Umido": the leading code names the service.
        type_key=lambda record: (
            str(record["tipologiaServizio"]).split(" - ")[0].strip()
        ),
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "UMI": wt.ORGANIC,
            "VER": wt.GARDEN_WASTE,
            "CAR": wt.PAPER,
            "VET": wt.GLASS,
            # Multipak: plastic and metal packaging collected together.
            "MUL": wt.RECYCLABLES,
            "APL": wt.PLASTIC,
            "SEC": wt.GENERAL_WASTE,
            "ECU": wt.GENERAL_WASTE,
            "STP": wt.GENERAL_WASTE,
            # Manual and mechanical street sweeping.
            "MAN": wt.OTHER,
            "SPA": wt.OTHER,
        },
    )
