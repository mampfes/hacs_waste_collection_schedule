"""Waste collection schedules from the Comune Smart / Internavigare platform.

Municipalities are identified by public app access tokens. Currently, Capri
Leone is the only municipality with a verified, populated waste calendar.
"""

from typing import ClassVar, TypedDict, final

from waste_collection_schedule import config_params, date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

_EVENTS_URL = "https://comuni.internavigare.com/backend/api/v1/rifiuti-evento"
_CAPRI_LEONE_TOKEN = "n-PRl8rIpm"


class _WasteEvent(TypedDict):
    data: str
    titolo: str


@final
class Source(BaseSource):
    TITLE = "Comune Smart"
    DESCRIPTION = "Waste collection schedules from the Comune Smart app platform."
    URL = "https://comunesmart.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@otakon87"]

    TEST_CASES: ClassVar[dict] = {
        "Capri Leone": {"access_token": _CAPRI_LEONE_TOKEN},
    }
    REGIONS = (
        region(
            "Capri Leone",
            access_token=_CAPRI_LEONE_TOKEN,
            url="https://comune.caprileone.me.it",
        ),
    )
    PARAMS = (
        config_params.text_field("access_token", label="Municipality access token"),
    )
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
        wt.METAL,
        wt.GENERAL_WASTE,
    ]

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Select a supported municipality to pre-fill its public app access token. "
            "Currently, Capri Leone (ME) has a verified waste collection calendar."
        ),
        "it": (
            "Seleziona un comune supportato per precompilare il token pubblico "
            "dell'app. Attualmente è verificato il calendario di Capri Leone (ME)."
        ),
    }

    retrieve = HttpGetRetriever(
        url=_EVENTS_URL,
        params=lambda access_token, **_: {"access-token": access_token},
    )
    parse = parsers.JsonParser(shape=list[_WasteEvent])
    transform = JsonTransformer(
        date_key="data",
        type_key="titolo",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Ritiro Organico": wt.ORGANIC,
            "Ritiro Plastica": wt.PLASTIC,
            "Ritiro Carta e Cartone": wt.PAPER,
            "Ritiro Vetro e Lattine": [wt.GLASS, wt.METAL],
            "Ritiro Indifferenziato": wt.GENERAL_WASTE,
        },
    )
