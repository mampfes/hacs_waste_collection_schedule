import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.service.NorkartMinRenovasjon import MinRenovasjonParser
from waste_collection_schedule.transformers import RowTransformer

SEARCH_URL = "https://fritekstsok.api.norkart.no/search/kommunecustom"
FRACTIONS_URL = "https://mdt-proxy.movar.no/api/Fraksjoner"
CALENDAR_URL = "https://mdt-proxy.movar.no/api/Tommekalender"

# The public tokens movar.no's own calendar page sends.
API_TOKEN = "e6727744-e3f9-4162-a43f-3480fdb1861d"

_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Papp og papir": wt.PAPER,
    "Papp": wt.PAPER,
    "Matavfall": wt.FOOD_WASTE,
    "Våtorganisk": wt.FOOD_WASTE,
    "Glass og metallemballasje": wt.RECYCLABLES,
    "Drikkekartonger": wt.CARTONS,
    "Spesialavfall": wt.HAZARDOUS,
    "Plastemballasje": wt.PLASTIC,
    "Hageavfall": wt.GARDEN_WASTE,
    "Metaller": wt.METAL,
}


def _address_hit(response, *_, address, **__):
    """The first address the search matches: its street, number and municipality."""
    results = response.json()["SearchResults"]
    if not results:
        raise SourceArgumentNotFound("address", address)
    return results[0]["Source"]


@final
class Source(BaseSource):
    TITLE = "Movar IKS"
    DESCRIPTION = "Source script for movar.no"
    URL = "https://movar.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Vålerveien 1148, Våler": {"address": "Vålerveien 1148, Våler"},
        "Skråtorpveien 20A, Råde": {"address": "Skråtorpveien 20A, Råde"},
    }

    PARAMS = (street_address(),)

    retrieve = FanOutRetriever(
        prepare=Lookup(
            SEARCH_URL,
            params=lambda address, **_: {
                "Targets": "gateadresse",
                "Query": address,
                "Size": "100",
            },
            headers={"accept": "application/json", "x-waapi-token": API_TOKEN},
            pick=_address_hit,
        ),
        targets=lambda source, hit: ("fractions", "calendar"),
        fetch=Request(
            lambda target, hit, **_: (
                FRACTIONS_URL if target == "fractions" else CALENDAR_URL
            ),
            params=lambda target, hit, **_: (
                {"apitoken": API_TOKEN}
                if target == "fractions"
                else {
                    "dato": f"{datetime.date.today().year + 1}-12-31T23:59:59+11:00",
                    "gatenavn": hit["GateNavn"],
                    "husnr": str(hit["AdresseHusNummer"]),
                    "apitoken": API_TOKEN,
                }
            ),
            headers=lambda target, hit, **_: {
                "accept": "application/json",
                "kommunenr": str(hit["KommuneNummer"]),
            },
        ),
    )
    parse = MinRenovasjonParser()
    transform = RowTransformer(type_value_map=_TYPE_MAP)
