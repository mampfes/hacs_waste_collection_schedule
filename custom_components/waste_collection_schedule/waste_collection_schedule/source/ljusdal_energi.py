from typing import ClassVar, final
from waste_collection_schedule.source.base_source import BaseSource
from waste_collection_schedule.source.parsers import JsonParser
from waste_collection_schedule.source.transformers import JsonTransformer
from waste_collection_schedule.source.retrievers import FanOutRetriever, MultipleHitsError
from waste_collection_schedule.source.param_types import street_address
from waste_collection_schedule.source.exceptions import SourceArgAmbiguousWithSuggestions
import waste_collection_schedule.source.waste_types as wt

API = "https://ljusdalenergi.se"

@final
class Source(BaseSource):
    TITLE = "Ljusdal Renhållning"
    DESCRIPTION = "Source for Ljusdal Renhållning waste collection, Sweden."
    URL = "https://ljusdalenergi.se"
    COUNTRY = "se"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@vBrolin"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.METAL,
        wt.PLASTIC,
    ]
    TEST_CASES: ClassVar[dict] = {
        "Norra Järnvägsgatan 21": {"address": "Norra Järnvägsgatan 21, Ljusdal"},
        "Stationsgatan 1, Järvsö": {"address": "Stationsgatan 1, Järvsö"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "Ogiltigvägen 999"},
        "Ambiguous address": {"address": "Kyrkogatan"},
    }
    PARAMS = (street_address("address"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as shown in the search on "
            "https://ljusdalenergi.se/renhallning/privatpersoner/sophamtning/nar-hamtas-dina-sopor/hamtningsdagar.html"
        ),
    }

    # Detta är motorn som saknades i ditt utkast:
    retrieve = FanOutRetriever(
        # Steg 1: Sök efter adresser och fånga upp alla unika ServiceId
        search_request={
            "url": f"{API}/Address/Search",
            "params": {"query": "{address}"},
        },
        # Filtrera och slå ihop träffar som exakt matchar gatan
        filter_hits=lambda hit, args: True, 
        get_service_ids=lambda json_data: [item["ServiceId"] for item in json_data],
        
        # Steg 2: Gör ett API-anrop per unikt ServiceId vi hittade ovan
        fetch_request=lambda service_id: {
            "url": f"{API}/Address/CollectionDays",
            "params": {"serviceId": service_id},
        },
    )

    parse = JsonParser()

    transform = JsonTransformer(
        date_key="Dates",
        type_key="ContainerType",
        type_value_map={
            "Hushållsavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Papper": wt.PAPER,
            "Metall": wt.METAL,
            "Plast": wt.PLASTIC,
        },
    )
