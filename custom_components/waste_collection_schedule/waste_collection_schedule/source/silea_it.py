from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer

API = "https://www.sileaspa.it/wp-admin/admin-ajax.php"


def _match(response, argument, value):
    records = response.json()
    for item in records:
        if value.lower() in item["name"].lower():
            return item["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        argument, value, [item["name"].title() for item in records]
    )


@final
class Source(BaseSource):
    TITLE = "Silea"
    DESCRIPTION = "Silea"
    URL = "https://www.sileaspa.it"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"municipality": "Lomagna", "address": "via martiri"},
        "Test_002": {"municipality": "Cesana", "address": "via ugo foscolo"},
    }
    COUNTRY = "it"
    PARAMS = (municipality(), street_address())
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.PAPER,
        wt.FOOD_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your municipality and street as listed at https://www.sileaspa.it. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(
                API,
                method="POST",
                data={"action": "get_comuni"},
                pick=lambda response, municipality, **_: _match(
                    response, "municipality", municipality
                ),
            ),
            retrievers.Lookup(
                API,
                method="POST",
                data=lambda town, **_: {"action": "get_vie", "id_cliente": town},
                pick=lambda response, town, address, **_: _match(
                    response, "address", address
                ),
            ),
            retrievers.Lookup(
                API,
                method="POST",
                data=lambda town, street, **_: {
                    "action": "get_months",
                    "id_cliente": town,
                    "id_via": street,
                },
                pick=lambda response, *_, **__: response.json(),
            ),
        ),
        targets=lambda source, context: context[2],
        fetch=retrievers.Request(
            API,
            method="POST",
            data=lambda target, context, **_: {
                "action": "get_calendar",
                "id_cliente": context[0],
                "id_via": context[1],
                "id_mese": target["id"],
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser())
    preprocess = preprocessors.ExplodeList("services", into="service")
    transform = JsonTransformer(
        date_key="format",
        type_key=lambda record: record["service"].get("service", "").strip(),
        skip_unparseable_dates=True,
        type_value_map={
            "INDIFFERENZIATO": wt.GENERAL_WASTE,
            "PLASTICA, LATTINE E TETRAPAK": wt.RECYCLABLES,
            "VETRO": wt.GLASS,
            "CARTA E CARTONE": wt.PAPER,
            "SPAZZAMENTO MECCANIZZATO": wt.GENERAL_WASTE,
            "UMIDO": wt.FOOD_WASTE,
        },
    )
